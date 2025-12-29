"""
API эндпоинты для работы с историей генераций.

Получение списка генераций и скачивание файлов.

Два типа эндпоинтов:
1. JWT авторизация (веб) — GET /api/v1/generations/
2. Bot Secret авторизация — GET /api/v1/generations/bot/{telegram_id}
"""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, verify_bot_secret
from app.db.database import get_db
from app.db.models import User, UserPlan
from app.models.schemas import GenerationListResponse, GenerationResponse
from app.repositories import GenerationRepository, UserRepository

router = APIRouter(prefix="/api/v1/generations", tags=["Generations"])

# Безопасная работа с файлами — защита от Path Traversal
ALLOWED_DIR = Path("data/generations").resolve()


async def _get_gen_repo(db: AsyncSession = Depends(get_db)) -> GenerationRepository:
    """Dependency для получения GenerationRepository."""
    return GenerationRepository(db)


async def _get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency для получения UserRepository."""
    return UserRepository(db)


@router.get("", response_model=GenerationListResponse)
async def list_generations(
    page: int = 1,
    limit: int = 10,
    user: User = Depends(get_current_user),
    gen_repo: GenerationRepository = Depends(_get_gen_repo),
) -> GenerationListResponse:
    """
    Получить список генераций текущего пользователя.

    Параметры:
    - page: Номер страницы (начиная с 1)
    - limit: Количество записей на странице (максимум 100)

    Возвращает:
    - items: Список генераций
    - total: Общее количество генераций
    """
    # Ограничиваем limit
    limit = min(limit, 100)

    items, total = await gen_repo.get_user_generations(user.id, page, limit)

    return GenerationListResponse(
        items=[
            GenerationResponse(
                id=g.id,
                user_id=g.user_id,
                labels_count=g.labels_count,
                file_path=g.file_path,
                preflight_passed=g.preflight_passed,
                expires_at=g.expires_at,
                created_at=g.created_at,
            )
            for g in items
        ],
        total=total,
    )


@router.get("/{generation_id}/download")
async def download_generation(
    generation_id: UUID,
    user: User = Depends(get_current_user),
    gen_repo: GenerationRepository = Depends(_get_gen_repo),
) -> FileResponse:
    """
    Скачать PDF файл генерации.

    Параметры:
    - generation_id: UUID генерации

    Возвращает:
    - PDF файл для скачивания

    Ошибки:
    - 404: Генерация не найдена или принадлежит другому пользователю
    - 410: Файл удалён (срок хранения 7 дней)
    """
    generation = await gen_repo.get_by_id(generation_id)

    # Проверяем существование и принадлежность
    if not generation or generation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Генерация не найдена",
        )

    # Проверяем наличие файла
    if not generation.file_path:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Файл не был сохранён",
        )

    # Проверяем что файл находится внутри разрешённой директории (Path Traversal защита)
    file_path = Path(generation.file_path).resolve()
    if not file_path.is_relative_to(ALLOWED_DIR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён",
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Файл удалён (срок хранения 7 дней)",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"labels_{generation_id}.pdf",
    )


# === Bot endpoints (по telegram_id, защита через X-Bot-Secret) ===


@router.get(
    "/bot/{telegram_id}",
    response_model=GenerationListResponse,
    dependencies=[Depends(verify_bot_secret)],
)
async def list_generations_by_telegram(
    telegram_id: int,
    limit: int = 5,
    offset: int = 0,
    user_repo: UserRepository = Depends(_get_user_repo),
    gen_repo: GenerationRepository = Depends(_get_gen_repo),
) -> GenerationListResponse:
    """
    Получить список генераций пользователя по telegram_id.

    Доступно только для Pro и Enterprise пользователей.
    Free пользователи не имеют сохранённой истории.

    Параметры:
    - telegram_id: ID пользователя в Telegram
    - limit: Количество записей (по умолчанию 5, максимум 100)
    - offset: Смещение от начала

    Возвращает:
    - items: Список генераций
    - total: Общее количество генераций
    """
    # Находим пользователя по telegram_id
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    # Free пользователям история недоступна
    if user.plan == UserPlan.FREE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="История доступна только на тарифах Pro и Enterprise",
        )

    # Ограничиваем limit
    limit = min(limit, 100)

    # Вычисляем page из offset
    page = (offset // limit) + 1 if limit > 0 else 1

    items, total = await gen_repo.get_user_generations(user.id, page, limit)

    return GenerationListResponse(
        items=[
            GenerationResponse(
                id=g.id,
                user_id=g.user_id,
                labels_count=g.labels_count,
                file_path=g.file_path,
                preflight_passed=g.preflight_passed,
                expires_at=g.expires_at,
                created_at=g.created_at,
            )
            for g in items
        ],
        total=total,
    )


@router.get(
    "/bot/{telegram_id}/{generation_id}/download",
    dependencies=[Depends(verify_bot_secret)],
)
async def download_generation_by_telegram(
    telegram_id: int,
    generation_id: UUID,
    user_repo: UserRepository = Depends(_get_user_repo),
    gen_repo: GenerationRepository = Depends(_get_gen_repo),
) -> FileResponse:
    """
    Скачать PDF файл генерации по telegram_id.

    Параметры:
    - telegram_id: ID пользователя в Telegram
    - generation_id: UUID генерации

    Возвращает:
    - PDF файл для скачивания

    Ошибки:
    - 404: Пользователь или генерация не найдены
    - 403: Free план или генерация принадлежит другому пользователю
    - 410: Файл удалён (срок хранения истёк)
    """
    # Находим пользователя по telegram_id
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    # Free пользователям история недоступна
    if user.plan == UserPlan.FREE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="История доступна только на тарифах Pro и Enterprise",
        )

    # Получаем генерацию
    generation = await gen_repo.get_by_id(generation_id)

    # Проверяем существование и принадлежность
    if not generation or generation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Генерация не найдена",
        )

    # Проверяем наличие файла
    if not generation.file_path:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Файл не был сохранён",
        )

    # Проверяем что файл находится внутри разрешённой директории (Path Traversal защита)
    file_path = Path(generation.file_path).resolve()
    if not file_path.is_relative_to(ALLOWED_DIR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён",
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Файл удалён (срок хранения истёк)",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"labels_{generation_id}.pdf",
    )
