"""
Celery задачи для генерации этикеток.

Используется для асинхронной обработки больших файлов (>60 кодов).
"""

import base64
import hashlib
import logging
import os
import uuid
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.celery_app import celery
from app.config import get_settings
from app.db.models import Generation, ProductCard, Task, TaskStatus, UsageLog, User, UserPlan

logger = logging.getLogger(__name__)

# Константы
TASK_SOFT_LIMIT = 600  # 10 минут
TASK_HARD_LIMIT = 660  # 11 минут
# Директория для сохранения результатов (относительный путь, как в labels.py)
GENERATIONS_DIR = "data/generations"

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


def _should_autosave_products_sync(user: User | None) -> bool:
    """
    Проверить можно ли автосохранять карточки для пользователя.

    Автосохранение доступно только для PRO и ENTERPRISE тарифов.
    """
    if not user:
        return False
    return user.plan in (UserPlan.PRO, UserPlan.ENTERPRISE)


def _extract_unique_products_for_save_sync(label_items: list) -> list[dict]:
    """
    Извлечь уникальные товары для сохранения в базу карточек.

    Дедупликация по barcode — если один товар встречается несколько раз
    (несколько кодов ЧЗ для одного баркода), сохраняем только один раз.

    Returns:
        Список словарей с полями для ProductCard
    """
    seen_barcodes: set[str] = set()
    products: list[dict] = []

    for item in label_items:
        if not item.barcode or item.barcode in seen_barcodes:
            continue

        seen_barcodes.add(item.barcode)
        products.append(
            {
                "barcode": item.barcode,
                "name": item.name,
                "article": item.article,
                "size": item.size,
                "color": item.color,
                "composition": item.composition,
                "country": item.country,
                "brand": item.brand,
                "manufacturer": item.manufacturer,
                "production_date": item.production_date,
                "importer": item.importer,
                "certificate_number": item.certificate_number,
                "address": item.address,
            }
        )

    return products


def _autosave_products_sync(
    session: Session,
    user: User,
    label_items: list,
) -> dict | None:
    """
    Автосохранение карточек товаров после успешной генерации (синхронная версия).

    Args:
        session: Синхронная сессия БД
        user: Пользователь (PRO/ENTERPRISE)
        label_items: Список товаров из генерации

    Returns:
        Статистика {"created": N, "updated": M} или None при ошибке
    """
    if not _should_autosave_products_sync(user):
        return None

    products = _extract_unique_products_for_save_sync(label_items)
    if not products:
        return None

    try:
        # Синхронный bulk_upsert
        barcodes = [item.get("barcode") for item in products if item.get("barcode")]

        # Получаем существующие карточки
        existing_result = session.execute(
            select(ProductCard).where(
                ProductCard.user_id == user.id,
                ProductCard.barcode.in_(barcodes),
            )
        )
        existing = list(existing_result.scalars().all())
        existing_barcodes = {card.barcode for card in existing}

        created = 0
        updated = 0

        for item in products:
            barcode = item.get("barcode")
            if not barcode:
                continue

            # Подготавливаем данные для upsert
            data = {k: v for k, v in item.items() if k != "barcode" and v is not None}

            if barcode in existing_barcodes:
                # Обновляем существующую
                if data:
                    session.execute(
                        update(ProductCard)
                        .where(
                            ProductCard.user_id == user.id,
                            ProductCard.barcode == barcode,
                        )
                        .values(**data)
                    )
                    updated += 1
            else:
                # Создаём новую
                new_card = ProductCard(
                    user_id=user.id,
                    barcode=barcode,
                    **data,
                )
                session.add(new_card)
                created += 1
                existing_barcodes.add(barcode)  # Предотвращаем дубликаты в batch

        session.flush()
        session.commit()

        logger.info(
            f"[autosave] Сохранено карточек для user {user.id}: "
            f"created={created}, updated={updated}"
        )
        return {"created": created, "updated": updated}

    except Exception as e:
        logger.warning(f"[autosave] Ошибка сохранения карточек: {e}")
        session.rollback()
        return None


@celery.task(
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

        # Получаем задачу и пользователя для автосохранения карточек
        task_record = session.execute(select(Task).where(Task.id == task_uuid)).scalar_one_or_none()
        user: User | None = None
        if task_record and task_record.user_id:
            user = session.execute(
                select(User).where(User.id == task_record.user_id)
            ).scalar_one_or_none()

        # Декодируем Excel из base64
        excel_bytes = base64.b64decode(excel_bytes_b64)

        # Получаем результат preflight проверки (выполнена до async decision)
        preflight_ok = params.get("preflight_ok", True)

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
        # Логика идентична синхронной генерации (labels.py)
        relative_path = None
        numbering_mode = params.get("numbering_mode", "none")
        start_number = params.get("start_number", 1)

        if user:
            from datetime import timedelta
            from pathlib import Path

            user_dir = Path(GENERATIONS_DIR) / str(user.id)
            user_dir.mkdir(parents=True, exist_ok=True)

            result_filename = f"{task_id}.pdf"
            file_path = user_dir / result_filename

            with open(file_path, "wb") as f:
                f.write(pdf_bytes)

            relative_path = str(file_path)
            file_hash = hashlib.sha256(pdf_bytes).hexdigest()

            file_size_kb = len(pdf_bytes) / 1024
            logger.info(
                f"Задача {task_id}: сохранён результат {relative_path} ({file_size_kb:.1f} KB)"
            )

            # Сроки хранения как в синхронной: ENTERPRISE=30, PRO=7, FREE=None
            if user.plan == UserPlan.ENTERPRISE:
                expires_days = 30
            elif user.plan == UserPlan.PRO:
                expires_days = 7
            else:
                expires_days = None  # FREE — не сохраняем в историю

            # Создаём Generation только для PRO/ENTERPRISE (как в синхронной)
            if expires_days is not None:
                generation = Generation(
                    user_id=user.id,
                    labels_count=labels_count,
                    file_path=relative_path,
                    file_hash=file_hash,
                    file_size_bytes=len(pdf_bytes),
                    preflight_passed=preflight_ok,
                    expires_at=datetime.now(UTC) + timedelta(days=expires_days),
                )
                session.add(generation)
                logger.info(f"Задача {task_id}: создана запись в истории")

            # Записываем статистику использования (для всех тарифов)
            usage_log = UsageLog(
                user_id=user.id,
                labels_count=labels_count,
                preflight_status="ok" if preflight_ok else "error",
            )
            session.add(usage_log)
            logger.info(f"Задача {task_id}: записана статистика ({labels_count} этикеток)")

            # === АВТОСОХРАНЕНИЕ КАРТОЧЕК ===
            if _should_autosave_products_sync(user):
                autosave_result = _autosave_products_sync(
                    session=session,
                    user=user,
                    label_items=label_items,
                )
                if autosave_result:
                    logger.info(
                        f"Задача {task_id}: автосохранение карточек: "
                        f"created={autosave_result['created']}, updated={autosave_result['updated']}"
                    )

            # === СОХРАНЕНИЕ last_serial_number (как в синхронной) ===
            # Для режимов per_product и continue
            if numbering_mode in ("per_product", "continue") and user.plan in (
                UserPlan.PRO,
                UserPlan.ENTERPRISE,
            ):
                # Строим products_map из label_items
                products_map: dict[str, Any] = {}
                for item in label_items:
                    if item.barcode:
                        products_map[item.barcode] = item

                if products_map:
                    final_serials: dict[str, int] = {}

                    def extract_barcode_from_code(code: str) -> str | None:
                        """GTIN (01 + 14 цифр) → EAN-13 barcode."""
                        if code.startswith("01") and len(code) >= 16:
                            gtin = code[2:16]
                            barcode = gtin.lstrip("0")
                            if barcode in products_map:
                                return barcode
                            if gtin in products_map:
                                return gtin
                        return None

                    if numbering_mode == "per_product":
                        barcode_counts: Counter[str] = Counter()
                        for code in codes_list:
                            barcode = extract_barcode_from_code(code)
                            if barcode:
                                barcode_counts[barcode] += 1
                        final_serials = dict(barcode_counts)

                    elif numbering_mode == "continue":
                        barcode_last_positions: dict[str, int] = {}
                        for idx, code in enumerate(codes_list):
                            barcode = extract_barcode_from_code(code)
                            if barcode:
                                barcode_last_positions[barcode] = idx

                        for barcode, last_idx in barcode_last_positions.items():
                            final_serials[barcode] = start_number + last_idx

                    # Обновляем карточки в БД
                    for barcode, last_serial in final_serials.items():
                        try:
                            session.execute(
                                update(ProductCard)
                                .where(
                                    ProductCard.user_id == user.id,
                                    ProductCard.barcode == barcode,
                                )
                                .values(last_serial_number=last_serial)
                            )
                            logger.info(
                                f"Задача {task_id}: обновлён last_serial_number: {barcode} -> {last_serial}"
                            )
                        except Exception as e:
                            logger.warning(
                                f"Задача {task_id}: не удалось обновить serial: {barcode}, {e}"
                            )

            # === ОБНОВЛЕНИЕ last_label_number (как в синхронной) ===
            # Для режимов sequential и continue
            if numbering_mode in ("sequential", "continue") and start_number:
                new_last_number = start_number + labels_count - 1
                if (user.last_label_number or 0) < new_last_number:
                    session.execute(
                        update(User)
                        .where(User.id == user.id)
                        .values(last_label_number=new_last_number)
                    )
                    logger.info(f"Задача {task_id}: обновлён last_label_number: {new_last_number}")

            session.commit()

        else:
            # Для анонимных пользователей — временная директория
            import tempfile

            temp_dir = tempfile.mkdtemp(prefix="kleykod_")
            result_filename = f"{task_id}.pdf"
            result_path = os.path.join(temp_dir, result_filename)

            with open(result_path, "wb") as f:
                f.write(pdf_bytes)

            relative_path = result_path
            file_size_kb = len(pdf_bytes) / 1024
            logger.info(
                f"Задача {task_id}: сохранён результат {result_path} ({file_size_kb:.1f} KB)"
            )

        # Помечаем задачу как завершённую
        update_task_status(
            session,
            task_uuid,
            TaskStatus.COMPLETED,
            progress=100,
            result_path=relative_path,
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


@celery.task
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


# Порог для определения "застрявшей" задачи (минуты)
STUCK_TASK_THRESHOLD_MINUTES = 10


@celery.task
def recover_stuck_tasks() -> dict:
    """
    Восстановление застрявших задач.

    Задача считается "застрявшей" если:
    - Статус PENDING и прошло более 10 минут с момента создания
    - Статус PROCESSING и прошло более 15 минут с момента начала

    Такие задачи помечаются как FAILED с соответствующим сообщением.
    Запускается по расписанию (celery beat) каждые 5 минут.
    """
    from datetime import timedelta

    from sqlalchemy import and_, or_, select

    session = get_sync_session()
    recovered_count = 0

    try:
        now = datetime.now(UTC)
        pending_threshold = now - timedelta(minutes=STUCK_TASK_THRESHOLD_MINUTES)
        processing_threshold = now - timedelta(minutes=STUCK_TASK_THRESHOLD_MINUTES + 5)

        # Находим застрявшие задачи
        stuck_tasks = (
            session.execute(
                select(Task).where(
                    or_(
                        # PENDING дольше 10 минут
                        and_(
                            Task.status == TaskStatus.PENDING,
                            Task.created_at < pending_threshold,
                        ),
                        # PROCESSING дольше 15 минут (без прогресса)
                        and_(
                            Task.status == TaskStatus.PROCESSING,
                            Task.started_at < processing_threshold,
                        ),
                    )
                )
            )
            .scalars()
            .all()
        )

        for task in stuck_tasks:
            old_status = task.status
            task.status = TaskStatus.FAILED
            task.completed_at = now
            task.error_message = (
                f"Задача застряла в статусе {old_status.value}. "
                "Попробуйте загрузить файлы заново."
            )
            recovered_count += 1
            logger.warning(
                f"Задача {task.id} помечена как FAILED "
                f"(была {old_status.value} с {task.created_at})"
            )

        if recovered_count > 0:
            session.commit()
            logger.info(f"Recovery: помечено как FAILED {recovered_count} застрявших задач")

        return {"recovered": recovered_count}

    except Exception as e:
        logger.exception(f"Ошибка recovery: {e}")
        session.rollback()
        return {"error": str(e)}

    finally:
        session.close()
