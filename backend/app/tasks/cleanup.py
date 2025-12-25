"""
Задача очистки истекших генераций.

Удаляет PDF файлы и записи старше 7 дней.
"""

import asyncio
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_factory
from app.repositories import GenerationRepository

logger = logging.getLogger(__name__)


async def cleanup_expired_generations(session: AsyncSession) -> int:
    """
    Удаляет генерации с истекшим сроком хранения.

    Args:
        session: Сессия базы данных

    Returns:
        Количество удалённых генераций
    """
    gen_repo = GenerationRepository(session)

    # Получаем истекшие генерации
    expired = await gen_repo.get_expired()

    if not expired:
        logger.debug("Нет истекших генераций для удаления")
        return 0

    deleted_count = 0

    for generation in expired:
        try:
            # Удаляем файл с диска
            if generation.file_path:
                file_path = Path(generation.file_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Удалён файл: {file_path}")

                # Удаляем пустую директорию пользователя
                parent_dir = file_path.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                    logger.debug(f"Удалена пустая директория: {parent_dir}")

            # Удаляем запись из БД
            await gen_repo.delete(generation.id)
            deleted_count += 1

        except Exception as e:
            logger.error(f"Ошибка при удалении генерации {generation.id}: {e}")
            continue

    await session.commit()
    logger.info(f"Очистка завершена: удалено {deleted_count} генераций")

    return deleted_count


async def run_cleanup_once() -> int:
    """
    Запускает очистку один раз.

    Создаёт сессию БД и выполняет очистку.

    Returns:
        Количество удалённых генераций
    """
    async with async_session_factory() as session:
        return await cleanup_expired_generations(session)


async def start_cleanup_loop(interval_hours: int = 24) -> None:
    """
    Запускает фоновый цикл очистки.

    Args:
        interval_hours: Интервал между запусками в часах (по умолчанию 24)
    """
    interval_seconds = interval_hours * 3600

    logger.info(f"Запущен цикл очистки генераций (интервал: {interval_hours}ч)")

    while True:
        try:
            deleted = await run_cleanup_once()
            if deleted > 0:
                logger.info(f"Очистка: удалено {deleted} истекших генераций")
        except Exception as e:
            logger.error(f"Ошибка в цикле очистки: {e}")

        await asyncio.sleep(interval_seconds)
