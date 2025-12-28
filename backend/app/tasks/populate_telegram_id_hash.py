"""
Задача миграции данных: заполнение telegram_id_hash для существующих пользователей.

Fernet шифрование не детерминистическое, поэтому для поиска пользователей
по telegram_id используем SHA-256 хеш. Эта задача заполняет хеши для
пользователей, у которых они ещё не установлены.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.utils.encryption import hash_telegram_id

logger = logging.getLogger(__name__)


async def populate_telegram_id_hashes(db: AsyncSession) -> int:
    """
    Заполнить telegram_id_hash для пользователей с NULL значением.

    Выполняется при старте приложения для миграции существующих данных.

    Args:
        db: Асинхронная сессия БД

    Returns:
        Количество обновлённых пользователей
    """
    # Находим пользователей без telegram_id_hash
    result = await db.execute(select(User).where(User.telegram_id_hash.is_(None)))
    users = result.scalars().all()

    if not users:
        return 0

    updated_count = 0
    for user in users:
        try:
            # telegram_id автоматически расшифровывается при чтении (EncryptedString)
            raw_telegram_id = user.telegram_id
            if raw_telegram_id:
                # Вычисляем и устанавливаем хеш
                user.telegram_id_hash = hash_telegram_id(raw_telegram_id)
                updated_count += 1
                logger.debug(f"Хеш установлен для пользователя {user.id}")
        except Exception as e:
            logger.warning(f"Не удалось установить хеш для пользователя {user.id}: {e}")

    if updated_count > 0:
        await db.flush()
        logger.info(f"Заполнено telegram_id_hash для {updated_count} пользователей")

    return updated_count
