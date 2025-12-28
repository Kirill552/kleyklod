"""
API эндпоинты для управления API ключами.

Позволяет Enterprise пользователям создавать, просматривать и отзывать ключи.

Два режима доступа:
1. JWT авторизация (для веб-интерфейса) — POST/GET/DELETE /api/v1/keys/
2. По telegram_id (для бота) — POST/GET/DELETE /api/v1/keys/bot/{telegram_id}
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, verify_bot_secret
from app.db.database import get_db
from app.db.models import User, UserPlan
from app.repositories import UserRepository
from app.services.api_keys import ApiKeyService

router = APIRouter(prefix="/api/v1/keys")


# === Pydantic модели ===


class ApiKeyCreatedResponse(BaseModel):
    """Ответ при создании API ключа."""

    api_key: str
    warning: str


class ApiKeyInfoResponse(BaseModel):
    """Информация о существующем API ключе."""

    prefix: str | None
    created_at: datetime | None
    last_used_at: datetime | None


class MessageResponse(BaseModel):
    """Простой ответ с сообщением."""

    message: str


# === Эндпоинты ===


@router.post(
    "/",
    response_model=ApiKeyCreatedResponse,
    summary="Создать API ключ",
    description="""
    Создаёт новый API ключ для текущего пользователя.

    **Требования:**
    - Подписка Enterprise

    **Важно:**
    - Ключ показывается только один раз — сохраните его!
    - Если ключ уже существует, старый будет автоматически отозван
    """,
)
async def create_api_key(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreatedResponse:
    """Создать новый API ключ."""
    # Проверяем подписку Enterprise
    if current_user.plan != UserPlan.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API ключи доступны только для Enterprise подписки",
        )

    key_service = ApiKeyService(db)
    full_key = await key_service.create_key(current_user)

    return ApiKeyCreatedResponse(
        api_key=full_key,
        warning="Сохраните ключ! Он больше не будет показан.",
    )


@router.get(
    "/info",
    response_model=ApiKeyInfoResponse,
    summary="Информация о ключе",
    description="Получить информацию о текущем API ключе (без самого ключа).",
)
async def get_api_key_info(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ApiKeyInfoResponse:
    """Получить информацию о текущем ключе."""
    key_service = ApiKeyService(db)
    info = await key_service.get_key_info(current_user)

    if not info:
        return ApiKeyInfoResponse(prefix=None, created_at=None, last_used_at=None)

    return ApiKeyInfoResponse(**info)


@router.delete(
    "/",
    response_model=MessageResponse,
    summary="Отозвать API ключ",
    description="Отозвать текущий API ключ. После отзыва ключ перестанет работать.",
)
async def revoke_api_key(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Отозвать API ключ."""
    key_service = ApiKeyService(db)
    revoked = await key_service.revoke_key(current_user)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Активный API ключ не найден",
        )

    return MessageResponse(message="API ключ успешно отозван")


# === Эндпоинты для бота (по telegram_id) ===


async def _get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency для получения UserRepository."""
    return UserRepository(db)


@router.post(
    "/bot/{telegram_id}",
    response_model=ApiKeyCreatedResponse,
    summary="Создать API ключ (для бота)",
    description="Создаёт API ключ для пользователя по telegram_id. Только для Enterprise.",
    dependencies=[Depends(verify_bot_secret)],
)
async def create_api_key_bot(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(_get_user_repo),
) -> ApiKeyCreatedResponse:
    """Создать API ключ через бота."""
    # Находим пользователя по telegram_id
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    # Проверяем подписку Enterprise
    if user.plan != UserPlan.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API ключи доступны только для Enterprise подписки",
        )

    key_service = ApiKeyService(db)
    full_key = await key_service.create_key(user)

    return ApiKeyCreatedResponse(
        api_key=full_key,
        warning="Сохраните ключ! Он больше не будет показан.",
    )


@router.get(
    "/bot/{telegram_id}",
    response_model=ApiKeyInfoResponse,
    summary="Информация о ключе (для бота)",
    description="Получить информацию о текущем API ключе по telegram_id.",
    dependencies=[Depends(verify_bot_secret)],
)
async def get_api_key_info_bot(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(_get_user_repo),
) -> ApiKeyInfoResponse:
    """Получить информацию о ключе через бота."""
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    key_service = ApiKeyService(db)
    info = await key_service.get_key_info(user)

    if not info:
        return ApiKeyInfoResponse(prefix=None, created_at=None, last_used_at=None)

    return ApiKeyInfoResponse(**info)


@router.delete(
    "/bot/{telegram_id}",
    response_model=MessageResponse,
    summary="Отозвать API ключ (для бота)",
    description="Отозвать API ключ по telegram_id.",
    dependencies=[Depends(verify_bot_secret)],
)
async def revoke_api_key_bot(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(_get_user_repo),
) -> MessageResponse:
    """Отозвать API ключ через бота."""
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    key_service = ApiKeyService(db)
    revoked = await key_service.revoke_key(user)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Активный API ключ не найден",
        )

    return MessageResponse(message="API ключ успешно отозван")
