"""
Репозиторий пользователей.

Обеспечивает CRUD операции для таблицы users.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User, UserPlan
from app.utils.encryption import hash_telegram_id, hash_vk_id

settings = get_settings()


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Получить пользователя по UUID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """
        Получить пользователя по Telegram ID.

        Поиск выполняется по детерминистическому SHA-256 хешу,
        так как Fernet шифрование не детерминистическое.
        """
        # Вычисляем хеш для поиска
        tg_hash = hash_telegram_id(telegram_id)
        result = await self.session.execute(select(User).where(User.telegram_id_hash == tg_hash))
        return result.scalar_one_or_none()

    async def get_by_vk_id(self, vk_user_id: int) -> User | None:
        """
        Получить пользователя по VK user ID.

        Поиск выполняется по детерминистическому SHA-256 хешу.
        """
        vk_hash = hash_vk_id(vk_user_id)
        result = await self.session.execute(select(User).where(User.vk_user_id_hash == vk_hash))
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        """
        Создать нового пользователя.

        Args:
            telegram_id: ID пользователя в Telegram
            username: Telegram username
            first_name: Имя
            last_name: Фамилия

        Returns:
            Созданный пользователь
        """
        now = datetime.now(UTC)

        user = User(
            telegram_id=str(telegram_id),
            telegram_id_hash=hash_telegram_id(telegram_id),  # Хеш для поиска
            telegram_username=username,
            first_name=first_name,
            last_name=last_name,
            plan=UserPlan.FREE,
            consent_given_at=now,  # При регистрации
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> tuple[User, bool]:
        """
        Получить или создать пользователя.

        Returns:
            (user, created): пользователь и флаг создания
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False

        user = await self.create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        return user, True

    async def create_from_vk(
        self,
        vk_user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        """
        Создать нового пользователя из VK.

        Args:
            vk_user_id: ID пользователя в VK
            first_name: Имя
            last_name: Фамилия

        Returns:
            Созданный пользователь
        """
        now = datetime.now(UTC)

        user = User(
            vk_user_id=str(vk_user_id),
            vk_user_id_hash=hash_vk_id(vk_user_id),
            first_name=first_name,
            last_name=last_name,
            plan=UserPlan.FREE,
            consent_given_at=now,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_or_create_vk(
        self,
        vk_user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> tuple[User, bool]:
        """
        Получить или создать пользователя из VK.

        Returns:
            (user, created): пользователь и флаг создания
        """
        user = await self.get_by_vk_id(vk_user_id)
        if user:
            return user, False

        user = await self.create_from_vk(
            vk_user_id=vk_user_id,
            first_name=first_name,
            last_name=last_name,
        )
        return user, True

    async def update_plan(
        self,
        user: User,
        plan: UserPlan,
        expires_at: datetime | None = None,
    ) -> User:
        """
        Обновить тарифный план пользователя.

        Args:
            user: Пользователь
            plan: Новый тариф
            expires_at: Срок действия (None для бессрочных)

        Returns:
            Обновлённый пользователь
        """
        user.plan = plan
        user.plan_expires_at = expires_at
        await self.session.flush()
        return user

    async def update_profile(
        self,
        user: User,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        """Обновить профиль пользователя."""
        if username is not None:
            user.telegram_username = username
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        await self.session.flush()
        return user

    async def deactivate(self, user: User) -> User:
        """Деактивировать пользователя."""
        user.is_active = False
        await self.session.flush()
        return user

    async def delete_personal_data(self, user: User) -> None:
        """
        Удалить персональные данные (право на забвение, 152-ФЗ).

        Заменяет ПДн на placeholder, сохраняя запись для статистики.
        """
        user.telegram_username = None
        user.first_name = None
        user.last_name = None
        user.email = None
        user.is_active = False
        await self.session.flush()

    async def check_plan_expired(self, user: User) -> bool:
        """Проверить, истёк ли срок подписки."""
        if user.plan == UserPlan.FREE:
            return False
        if user.plan_expires_at is None:
            return False
        return user.plan_expires_at < datetime.now(UTC)

    async def downgrade_expired_plans(self) -> int:
        """
        Понизить все истёкшие подписки до Free.

        Returns:
            Количество понижённых пользователей
        """
        from sqlalchemy import update

        now = datetime.now(UTC)
        result = await self.session.execute(
            update(User)
            .where(User.plan != UserPlan.FREE)
            .where(User.plan_expires_at < now)
            .values(plan=UserPlan.FREE, plan_expires_at=None)
        )
        await self.session.flush()
        return result.rowcount or 0

    async def update_preferences(self, user: User, fields: dict) -> User:
        """
        Обновить настройки генерации этикеток пользователя.

        Args:
            user: Пользователь
            fields: Словарь полей для обновления

        Returns:
            Обновлённый пользователь
        """
        for key, value in fields.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.session.flush()
        return user
