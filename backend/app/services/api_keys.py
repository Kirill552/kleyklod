"""
Сервис управления API ключами для Enterprise пользователей.

Ключ генерируется один раз и показывается пользователю.
В БД хранится только SHA-256 хеш для безопасности.
"""

import hashlib
import secrets
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiKey, User


def generate_api_key() -> tuple[str, str, str]:
    """
    Генерирует новый API ключ.

    Returns:
        (full_key, key_hash, key_prefix)
        - full_key: полный ключ для пользователя (показывается 1 раз)
        - key_hash: SHA-256 хеш для хранения в БД
        - key_prefix: первые 16 символов для отображения
    """
    random_part = secrets.token_hex(16)  # 32 символа
    full_key = f"kk_live_{random_part}"  # kk_live_abc123def456...
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:16]  # kk_live_abc123de

    return full_key, key_hash, key_prefix


class ApiKeyService:
    """Сервис для создания, отзыва и проверки API ключей."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_key(self, user: User) -> str:
        """
        Создает новый API ключ для пользователя.
        Если ключ уже есть — старый отзывается.

        Args:
            user: Пользователь

        Returns:
            Полный ключ (показывается пользователю ОДИН РАЗ)
        """
        # Удаляем старый ключ если есть
        await self.db.execute(delete(ApiKey).where(ApiKey.user_id == user.id))

        # Генерируем новый
        full_key, key_hash, key_prefix = generate_api_key()

        # Сохраняем в БД
        new_key = ApiKey(
            user_id=user.id,
            key_hash=key_hash,
            key_prefix=key_prefix,
        )
        self.db.add(new_key)
        await self.db.commit()

        return full_key

    async def revoke_key(self, user: User) -> bool:
        """
        Отзывает API ключ пользователя.

        Args:
            user: Пользователь

        Returns:
            True если ключ был отозван, False если ключа не было
        """
        result = await self.db.execute(delete(ApiKey).where(ApiKey.user_id == user.id))
        await self.db.commit()
        return result.rowcount > 0

    async def get_key_info(self, user: User) -> dict | None:
        """
        Получает информацию о ключе (без самого ключа).

        Args:
            user: Пользователь

        Returns:
            {prefix, created_at, last_used_at} или None
        """
        result = await self.db.execute(select(ApiKey).where(ApiKey.user_id == user.id))
        key_record = result.scalar_one_or_none()

        if not key_record:
            return None

        return {
            "prefix": key_record.key_prefix,
            "created_at": key_record.created_at,
            "last_used_at": key_record.last_used_at,
        }

    async def find_user_by_api_key(self, api_key: str) -> tuple[User, ApiKey] | None:
        """
        Находит пользователя по API ключу.

        Args:
            api_key: Полный API ключ

        Returns:
            (User, ApiKey) или None если ключ не найден
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        result = await self.db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash)
        )
        key_record = result.scalar_one_or_none()

        if not key_record:
            return None

        # Загружаем пользователя
        user_result = await self.db.execute(
            select(User).where(User.id == key_record.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return None

        return user, key_record

    async def update_last_used(self, key_record: ApiKey) -> None:
        """
        Обновляет время последнего использования ключа.

        Args:
            key_record: Запись API ключа
        """
        key_record.last_used_at = datetime.utcnow()
        await self.db.commit()
