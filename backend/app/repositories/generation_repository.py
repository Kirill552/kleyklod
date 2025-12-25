"""
Репозиторий генераций.

Обеспечивает CRUD операции для таблицы generations.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Generation


class GenerationRepository:
    """Репозиторий для работы с генерациями."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        labels_count: int,
        preflight_passed: bool = True,
        file_path: str | None = None,
        file_hash: str | None = None,
        file_size_bytes: int | None = None,
        expires_days: int = 7,
    ) -> Generation:
        """
        Создать запись о генерации.

        Args:
            user_id: ID пользователя
            labels_count: Количество этикеток
            preflight_passed: Прошла ли Pre-flight проверка
            file_path: Путь к файлу
            file_hash: SHA-256 хеш файла
            file_size_bytes: Размер файла
            expires_days: Срок хранения в днях

        Returns:
            Созданная генерация
        """
        generation = Generation(
            user_id=user_id,
            labels_count=labels_count,
            preflight_passed=preflight_passed,
            file_path=file_path,
            file_hash=file_hash,
            file_size_bytes=file_size_bytes,
            expires_at=datetime.now(UTC) + timedelta(days=expires_days),
        )
        self.session.add(generation)
        await self.session.commit()
        await self.session.refresh(generation)
        return generation

    async def get_by_id(self, generation_id: UUID) -> Generation | None:
        """Получить генерацию по ID."""
        result = await self.session.execute(
            select(Generation).where(Generation.id == generation_id)
        )
        return result.scalar_one_or_none()

    async def get_user_generations(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[Generation], int]:
        """
        Получить список генераций пользователя с пагинацией.

        Args:
            user_id: ID пользователя
            page: Номер страницы (начиная с 1)
            limit: Количество записей на странице

        Returns:
            (список генераций, общее количество)
        """
        offset = (page - 1) * limit

        # Общее количество
        count_result = await self.session.execute(
            select(func.count(Generation.id)).where(Generation.user_id == user_id)
        )
        total = count_result.scalar_one()

        # Список с пагинацией
        result = await self.session.execute(
            select(Generation)
            .where(Generation.user_id == user_id)
            .order_by(Generation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(result.scalars().all())

        return items, total

    async def get_expired(self) -> list[Generation]:
        """Получить просроченные генерации."""
        result = await self.session.execute(
            select(Generation).where(Generation.expires_at < datetime.now(UTC))
        )
        return list(result.scalars().all())

    async def delete(self, generation_id: UUID) -> None:
        """Удалить генерацию."""
        generation = await self.get_by_id(generation_id)
        if generation:
            await self.session.delete(generation)
            await self.session.commit()

    async def delete_expired(self) -> int:
        """
        Удалить все просроченные генерации.

        Returns:
            Количество удалённых записей
        """
        expired = await self.get_expired()
        count = len(expired)

        for gen in expired:
            await self.session.delete(gen)

        if count > 0:
            await self.session.commit()

        return count
