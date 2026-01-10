"""
Celery задачи для генерации этикеток.

Используется для асинхронной обработки больших файлов (>60 кодов).
"""

import base64
import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Task, TaskStatus

logger = logging.getLogger(__name__)

# Константы
TASK_SOFT_LIMIT = 600  # 10 минут
TASK_HARD_LIMIT = 660  # 11 минут
RESULT_DIR = "/tmp/kleykod_results"

# Порог для async обработки (количество кодов)
ASYNC_THRESHOLD_CODES = 60  # ~30 сек при 0.5 сек/код


def get_sync_session() -> Session:
    """Создать синхронную сессию БД для Celery worker."""
    settings = get_settings()
    # Конвертируем asyncpg URL в psycopg2
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(db_url)
    return Session(engine)


def update_task_status(
    session: Session,
    task_id: uuid.UUID,
    status: TaskStatus,
    progress: int | None = None,
    error_message: str | None = None,
    result_path: str | None = None,
    labels_count: int | None = None,
) -> None:
    """Обновить статус задачи в БД."""
    values: dict = {"status": status}

    if progress is not None:
        values["progress"] = progress

    if error_message is not None:
        values["error_message"] = error_message

    if result_path is not None:
        values["result_path"] = result_path

    if labels_count is not None:
        values["labels_count"] = labels_count

    if status == TaskStatus.PROCESSING:
        values["started_at"] = datetime.now(UTC)
    elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        values["completed_at"] = datetime.now(UTC)

    session.execute(update(Task).where(Task.id == task_id).values(**values))
    session.commit()


def update_task_progress(session: Session, task_id: uuid.UUID, progress: int) -> None:
    """Обновить прогресс задачи."""
    session.execute(
        update(Task).where(Task.id == task_id).values(progress=min(100, max(0, progress)))
    )
    session.commit()


@shared_task(
    bind=True,
    max_retries=2,
    soft_time_limit=TASK_SOFT_LIMIT,
    time_limit=TASK_HARD_LIMIT,
)
def generate_from_excel_async(
    self,
    task_id: str,
    excel_bytes_b64: str,
    codes_list: list[str],
    params: dict[str, Any],
) -> dict:
    """
    Асинхронная генерация этикеток из Excel.

    Полный pipeline:
    1. Парсим Excel → label_items
    2. Матчинг по GTIN
    3. Генерация PDF через LabelGenerator
    4. Сохранение результата

    Args:
        task_id: UUID задачи в БД
        excel_bytes_b64: Excel файл в base64 (для JSON сериализации)
        codes_list: Список кодов ЧЗ
        params: Параметры генерации (layout, size, show_* флаги и т.д.)

    Returns:
        Словарь с результатом
    """
    task_uuid = uuid.UUID(task_id)
    session = get_sync_session()

    try:
        # Помечаем задачу как обрабатываемую
        update_task_status(session, task_uuid, TaskStatus.PROCESSING, progress=0)
        logger.info(f"Задача {task_id}: начало обработки ({len(codes_list)} кодов)")

        # Декодируем Excel из base64
        excel_bytes = base64.b64decode(excel_bytes_b64)

        # Импорты внутри функции (для изоляции worker)
        from app.models.label_types import LabelLayout, LabelSize
        from app.services.excel_parser import ExcelBarcodeParser
        from app.services.label_generator import LabelGenerator, LabelItem

        # === ЭТАП 1: Парсинг Excel (10%) ===
        update_task_progress(session, task_uuid, 5)

        excel_parser = ExcelBarcodeParser()
        excel_data = excel_parser.parse(
            excel_bytes=excel_bytes,
            filename=params.get("excel_filename", "barcodes.xlsx"),
            column_name=params.get("barcode_column"),
        )

        update_task_progress(session, task_uuid, 10)

        # === ЭТАП 2: Подготовка LabelItems (20%) ===
        label_items: list[LabelItem] = []
        for item in excel_data.items:
            label_items.append(
                LabelItem(
                    barcode=item.barcode,
                    article=item.article or params.get("fallback_article"),
                    size=item.size or params.get("fallback_size"),
                    color=item.color or params.get("fallback_color"),
                    name=item.name,
                    brand=getattr(item, "brand", None),
                    country=item.country,
                    composition=item.composition,
                    manufacturer=getattr(item, "manufacturer", None),
                    production_date=getattr(item, "production_date", None),
                    importer=getattr(item, "importer", None),
                    certificate_number=getattr(item, "certificate_number", None),
                    address=getattr(item, "address", None),
                )
            )

        update_task_progress(session, task_uuid, 20)
        logger.info(f"Задача {task_id}: подготовлено {len(label_items)} товаров")

        # === ЭТАП 3: Генерация PDF (20-90%) ===
        try:
            layout_enum = LabelLayout(params.get("layout", "basic"))
        except ValueError:
            layout_enum = LabelLayout.BASIC

        try:
            size_enum = LabelSize(params.get("label_size", "58x40"))
        except ValueError:
            size_enum = LabelSize.SIZE_58x40

        label_generator = LabelGenerator()

        # Парсим кастомные строки
        custom_lines_list = params.get("custom_lines")

        # Прогресс будем обновлять по ходу генерации (внутри LabelGenerator это синхронно)
        update_task_progress(session, task_uuid, 30)

        pdf_bytes = label_generator.generate(
            items=label_items,
            codes=codes_list,
            size=size_enum.value,
            organization=params.get("organization_name"),
            inn=params.get("inn"),
            layout=layout_enum.value,
            label_format=params.get("label_format", "combined"),
            show_article=params.get("show_article", True),
            show_size=params.get("show_size", True),
            show_color=params.get("show_color", True),
            show_name=params.get("show_name", True),
            show_organization=params.get("show_organization", True),
            show_inn=params.get("show_inn", False),
            show_country=params.get("show_country", False),
            show_composition=params.get("show_composition", False),
            show_chz_code_text=params.get("show_chz_code_text", True),
            numbering_mode=params.get("numbering_mode", "none"),
            start_number=params.get("start_number", 1),
            show_brand=params.get("show_brand", False),
            show_importer=params.get("show_importer", False),
            show_manufacturer=params.get("show_manufacturer", False),
            show_address=params.get("show_address", False),
            show_production_date=params.get("show_production_date", False),
            show_certificate=params.get("show_certificate", False),
            organization_address=params.get("organization_address"),
            importer=params.get("importer_text"),
            manufacturer=params.get("manufacturer_text"),
            production_date=params.get("production_date_text"),
            certificate_number=params.get("certificate_number_text"),
            custom_lines=custom_lines_list,
        )

        update_task_progress(session, task_uuid, 90)
        labels_count = len(codes_list)
        logger.info(f"Задача {task_id}: сгенерировано {labels_count} этикеток")

        # === ЭТАП 4: Сохранение результата (90-100%) ===
        os.makedirs(RESULT_DIR, exist_ok=True)

        result_filename = f"{task_id}.pdf"
        result_path = os.path.join(RESULT_DIR, result_filename)

        with open(result_path, "wb") as f:
            f.write(pdf_bytes)

        file_size_kb = len(pdf_bytes) / 1024
        logger.info(f"Задача {task_id}: сохранён результат {result_path} ({file_size_kb:.1f} KB)")

        # Помечаем задачу как завершённую
        update_task_status(
            session,
            task_uuid,
            TaskStatus.COMPLETED,
            progress=100,
            result_path=result_path,
            labels_count=labels_count,
        )

        logger.info(f"Задача {task_id}: завершена успешно ({labels_count} этикеток)")

        return {
            "status": "completed",
            "labels_count": labels_count,
            "result_path": result_path,
        }

    except SoftTimeLimitExceeded:
        error_msg = "Превышено время обработки (10 мин)"
        logger.error(f"Задача {task_id}: {error_msg}")
        update_task_status(session, task_uuid, TaskStatus.FAILED, error_message=error_msg)
        return {"status": "failed", "error": error_msg}

    except Exception as e:
        error_msg = f"Ошибка генерации: {str(e)}"
        logger.exception(f"Задача {task_id}: {error_msg}")

        # Retry если есть попытки
        if self.request.retries < self.max_retries:
            logger.info(f"Задача {task_id}: retry {self.request.retries + 1}/{self.max_retries}")
            self.retry(countdown=10)

        update_task_status(session, task_uuid, TaskStatus.FAILED, error_message=error_msg)
        return {"status": "failed", "error": error_msg}

    finally:
        session.close()


@shared_task
def cleanup_old_tasks() -> dict:
    """
    Очистка старых задач и файлов.

    Запускается по расписанию (celery beat) раз в час.
    """
    session = get_sync_session()
    deleted_count = 0

    try:
        from sqlalchemy import select

        # Находим просроченные задачи
        expired_tasks = (
            session.execute(select(Task).where(Task.expires_at < datetime.now(UTC))).scalars().all()
        )

        for task in expired_tasks:
            # Удаляем файл результата если есть
            if task.result_path and os.path.exists(task.result_path):
                try:
                    os.remove(task.result_path)
                    logger.info(f"Удалён файл: {task.result_path}")
                except OSError as e:
                    logger.warning(f"Не удалось удалить файл {task.result_path}: {e}")

            # Удаляем задачу
            session.delete(task)
            deleted_count += 1

        session.commit()
        logger.info(f"Очистка: удалено {deleted_count} задач")

        return {"deleted": deleted_count}

    except Exception as e:
        logger.exception(f"Ошибка очистки: {e}")
        return {"error": str(e)}

    finally:
        session.close()
