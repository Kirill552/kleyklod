"""
Celery задачи для генерации этикеток.

Используется для асинхронной обработки больших PDF файлов.
"""

import logging
import os
import uuid
from datetime import UTC, datetime

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
def generate_labels_async(
    self,
    task_id: str,
    pdf_bytes_hex: str,
    total_pages: int,
) -> dict:
    """
    Асинхронная генерация этикеток из PDF.

    Args:
        task_id: UUID задачи в БД
        pdf_bytes_hex: PDF файл в hex-кодировке (для JSON сериализации)
        total_pages: Количество страниц для прогресс-бара

    Returns:
        Словарь с результатом
    """
    task_uuid = uuid.UUID(task_id)
    session = get_sync_session()

    try:
        # Помечаем задачу как обрабатываемую
        update_task_status(session, task_uuid, TaskStatus.PROCESSING, progress=0)
        logger.info(f"Задача {task_id}: начало обработки ({total_pages} страниц)")

        # Декодируем PDF из hex
        pdf_bytes = bytes.fromhex(pdf_bytes_hex)

        # Импортируем парсер
        from app.services.pdf_parser import PDFParser

        parser = PDFParser()

        # Парсим PDF с отчётом о прогрессе
        def progress_callback(processed: int, total: int) -> None:
            progress = int((processed / total) * 100)
            update_task_progress(session, task_uuid, progress)
            logger.debug(f"Задача {task_id}: прогресс {progress}%")

        # Извлекаем коды параллельно
        result = parser.extract_codes_parallel(
            pdf_bytes,
            remove_duplicates=True,
            max_workers=4,
            progress_callback=progress_callback,
        )

        codes = result.codes
        labels_count = len(codes)

        logger.info(f"Задача {task_id}: извлечено {labels_count} кодов")

        # Создаём директорию для результатов
        os.makedirs(RESULT_DIR, exist_ok=True)

        # Сохраняем результат (просто коды в файл для демо)
        # TODO: интегрировать полную генерацию PDF
        result_filename = f"{task_id}.txt"
        result_path = os.path.join(RESULT_DIR, result_filename)

        with open(result_path, "w") as f:
            f.write("\n".join(codes))

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
