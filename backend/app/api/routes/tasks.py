"""
API эндпоинты для управления фоновыми задачами.

Используется для polling статуса и скачивания результатов.
"""

import logging
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import TaskStatus, User
from app.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ===== Схемы =====


class TaskStatusResponse(BaseModel):
    """Ответ со статусом задачи."""

    id: str
    status: str
    progress: int
    result_url: str | None = None
    error: str | None = None
    labels_count: int | None = None

    model_config = {"from_attributes": True}


# ===== Зависимости =====


async def _get_task_repo(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    """Dependency для получения TaskRepository."""
    return TaskRepository(db)


# ===== Эндпоинты =====


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    summary="Получить статус задачи",
    description="Возвращает текущий статус, прогресс и ссылку на результат.",
)
async def get_task_status(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    task_repo: TaskRepository = Depends(_get_task_repo),
) -> TaskStatusResponse:
    """
    Получить статус задачи.

    Используется для polling прогресса долгих операций.
    """
    task = await task_repo.get_by_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена",
        )

    # Проверяем что задача принадлежит пользователю
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой задаче",
        )

    # Формируем URL для скачивания если задача завершена
    result_url = None
    if task.status == TaskStatus.COMPLETED and task.result_path:
        result_url = f"/api/v1/tasks/{task_id}/download"

    return TaskStatusResponse(
        id=str(task.id),
        status=task.status.value,
        progress=task.progress,
        result_url=result_url,
        error=task.error_message,
        labels_count=task.labels_count,
    )


@router.get(
    "/{task_id}/download",
    summary="Скачать результат задачи",
    description="Возвращает готовый файл если задача завершена.",
)
async def download_task_result(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    task_repo: TaskRepository = Depends(_get_task_repo),
) -> FileResponse:
    """
    Скачать результат задачи.

    Доступно только для завершённых задач с файлом результата.
    """
    task = await task_repo.get_by_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена",
        )

    # Проверяем что задача принадлежит пользователю
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой задаче",
        )

    # Проверяем что задача завершена
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Задача ещё не завершена (статус: {task.status.value})",
        )

    # Проверяем что файл существует
    if not task.result_path or not os.path.exists(task.result_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл результата не найден (возможно, срок хранения истёк)",
        )

    # Определяем имя файла для скачивания
    filename = f"labels_{task_id}.pdf"
    if task.result_path.endswith(".txt"):
        filename = f"codes_{task_id}.txt"

    logger.info(f"Скачивание результата задачи {task_id} пользователем {current_user.id}")

    return FileResponse(
        path=task.result_path,
        filename=filename,
        media_type="application/octet-stream",
    )
