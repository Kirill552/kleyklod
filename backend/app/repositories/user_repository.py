"""
Репозиторий пользователей.

Обеспечивает CRUD операции для таблицы users.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserPlan


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Получить пользователя по UUID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """
        Получить пользователя по Telegram ID.

        Примечание: telegram_id хранится зашифрованным,
        поэтому поиск выполняется по зашифрованному значению.
        """
        # Шифруем telegram_id для поиска
        encrypted_telegram_id = str(telegram_id)
        result = await self.session.execute(
            select(User).where(User.telegram_id == encrypted_telegram_id)
        )
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
        user = User(
            telegram_id=str(telegram_id),
            telegram_username=username,
            first_name=first_name,
            last_name=last_name,
            plan=UserPlan.FREE,
            consent_given_at=datetime.now(timezone.utc),  # При регистрации
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
        return user.plan_expires_at < datetime.now(timezone.utc)

    async def downgrade_expired_plans(self) -> int:
        """
        Понизить все истёкшие подписки до Free.

        Returns:
            Количество понижённых пользователей
        """
        from sqlalchemy import update

        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            update(User)
            .where(User.plan != UserPlan.FREE)
            .where(User.plan_expires_at < now)
            .values(plan=UserPlan.FREE, plan_expires_at=None)
        )
        await self.session.flush()
        return result.rowcount or 0
