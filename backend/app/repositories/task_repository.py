"""
Репозиторий фоновых задач.

Обеспечивает CRUD операции для таблицы tasks.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task, TaskStatus


class TaskRepository:
    """Репозиторий для работы с фоновыми задачами."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        total_pages: int | None = None,
        expires_hours: int = 24,
    ) -> Task:
        """
        Создать новую задачу.

        Args:
            user_id: ID пользователя
            total_pages: Количество страниц для обработки
            expires_hours: Срок хранения результата в часах

        Returns:
            Созданная задача
        """
        task = Task(
            user_id=user_id,
            total_pages=total_pages,
            status=TaskStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(hours=expires_hours),
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_by_id(self, task_id: UUID) -> Task | None:
        """Получить задачу по ID."""
        result = await self.session.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def update_status(
        self,
        task_id: UUID,
        status: TaskStatus,
        progress: int | None = None,
        error_message: str | None = None,
        result_path: str | None = None,
        labels_count: int | None = None,
    ) -> Task | None:
        """
        Обновить статус задачи.

        Args:
            task_id: ID задачи
            status: Новый статус
            progress: Прогресс (0-100)
            error_message: Сообщение об ошибке
            result_path: Путь к результату
            labels_count: Количество этикеток

        Returns:
            Обновлённая задача или None
        """
        values: dict = {"status": status}

        if progress is not None:
            values["progress"] = progress

        if error_message is not None:
            values["error_message"] = error_message

        if result_path is not None:
            values["result_path"] = result_path

        if labels_count is not None:
            values["labels_count"] = labels_count

        # Устанавливаем временные метки
        if status == TaskStatus.PROCESSING:
            values["started_at"] = datetime.now(UTC)
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            values["completed_at"] = datetime.now(UTC)

        await self.session.execute(update(Task).where(Task.id == task_id).values(**values))
        await self.session.commit()

        return await self.get_by_id(task_id)

    async def update_progress(self, task_id: UUID, progress: int) -> None:
        """
        Обновить прогресс задачи.

        Args:
            task_id: ID задачи
            progress: Прогресс (0-100)
        """
        await self.session.execute(
            update(Task).where(Task.id == task_id).values(progress=min(100, max(0, progress)))
        )
        await self.session.commit()

    async def complete(
        self,
        task_id: UUID,
        result_path: str,
        labels_count: int,
    ) -> Task | None:
        """
        Отметить задачу как завершённую.

        Args:
            task_id: ID задачи
            result_path: Путь к результату
            labels_count: Количество этикеток

        Returns:
            Обновлённая задача
        """
        return await self.update_status(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            result_path=result_path,
            labels_count=labels_count,
        )

    async def fail(self, task_id: UUID, error_message: str) -> Task | None:
        """
        Отметить задачу как неудавшуюся.

        Args:
            task_id: ID задачи
            error_message: Сообщение об ошибке

        Returns:
            Обновлённая задача
        """
        return await self.update_status(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=error_message,
        )

    async def get_expired(self) -> list[Task]:
        """Получить просроченные задачи."""
        result = await self.session.execute(select(Task).where(Task.expires_at < datetime.now(UTC)))
        return list(result.scalars().all())

    async def delete(self, task_id: UUID) -> None:
        """Удалить задачу."""
        task = await self.get_by_id(task_id)
        if task:
            await self.session.delete(task)
            await self.session.commit()

    async def delete_expired(self) -> int:
        """
        Удалить все просроченные задачи.

        Returns:
            Количество удалённых записей
        """
        expired = await self.get_expired()
        count = len(expired)

        for task in expired:
            await self.session.delete(task)

        if count > 0:
            await self.session.commit()

        return count
