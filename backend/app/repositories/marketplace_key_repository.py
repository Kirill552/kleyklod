"""
Репозиторий для работы с API ключами маркетплейсов.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketplaceKey, User
from app.utils.encryption import decrypt_field, encrypt_field


class MarketplaceKeyRepository:
    """Репозиторий для marketplace_keys."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_and_marketplace(
        self, user_id: uuid.UUID, marketplace: str
    ) -> MarketplaceKey | None:
        """Получить ключ по user_id и marketplace."""
        result = await self.db.execute(
            select(MarketplaceKey).where(
                MarketplaceKey.user_id == user_id,
                MarketplaceKey.marketplace == marketplace,
                MarketplaceKey.is_active is True,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user: User,
        marketplace: str,
        api_key: str,
    ) -> MarketplaceKey:
        """
        Создать новый ключ маркетплейса.

        Args:
            user: Пользователь
            marketplace: Маркетплейс (wb)
            api_key: API ключ (будет зашифрован)
        """
        # Деактивируем старый ключ если есть
        old_key = await self.get_by_user_and_marketplace(user.id, marketplace)
        if old_key:
            old_key.is_active = False

        # Создаём новый
        encrypted = encrypt_field(api_key)
        mk = MarketplaceKey(
            user_id=user.id,
            marketplace=marketplace,
            encrypted_api_key=encrypted,
        )
        self.db.add(mk)
        await self.db.commit()
        await self.db.refresh(mk)
        return mk

    async def get_decrypted_key(self, mk: MarketplaceKey) -> str:
        """Расшифровать и вернуть API ключ."""
        return decrypt_field(mk.encrypted_api_key)

    async def update_sync_stats(
        self,
        mk: MarketplaceKey,
        products_count: int,
    ) -> None:
        """Обновить статистику синхронизации."""
        mk.products_count = products_count
        mk.last_synced_at = datetime.now(UTC)
        await self.db.commit()

    async def deactivate(self, mk: MarketplaceKey) -> None:
        """Деактивировать ключ."""
        mk.is_active = False
        await self.db.commit()

    async def get_all_for_user(self, user_id: uuid.UUID) -> list[MarketplaceKey]:
        """Получить все активные ключи пользователя."""
        result = await self.db.execute(
            select(MarketplaceKey).where(
                MarketplaceKey.user_id == user_id,
                MarketplaceKey.is_active is True,
            )
        )
        return list(result.scalars().all())
