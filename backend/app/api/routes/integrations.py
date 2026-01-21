"""
API эндпоинты для интеграций с маркетплейсами.

Только для Enterprise пользователей.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, UserPlan
from app.repositories import MarketplaceKeyRepository
from app.repositories.product_repo import ProductRepository
from app.services.marketplace_api import WildberriesAPI, WildberriesAPIError

router = APIRouter(prefix="/api/v1/integrations")


# === Pydantic модели ===


class ConnectWBRequest(BaseModel):
    """Запрос на подключение WB."""

    api_key: str


class IntegrationInfo(BaseModel):
    """Информация об интеграции."""

    marketplace: str
    connected: bool
    products_count: int
    connected_at: datetime | None
    last_synced_at: datetime | None


class IntegrationsResponse(BaseModel):
    """Список интеграций."""

    integrations: list[IntegrationInfo]


class ConnectResponse(BaseModel):
    """Ответ на подключение."""

    success: bool
    message: str
    products_count: int


class SyncResponse(BaseModel):
    """Ответ на синхронизацию."""

    success: bool
    message: str
    synced_count: int
    new_count: int


class MessageResponse(BaseModel):
    """Простой ответ."""

    message: str


# === Helpers ===


def _require_enterprise(user: User) -> None:
    """Проверить что пользователь Enterprise."""
    if user.plan != UserPlan.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Интеграции доступны только для Enterprise подписки",
        )


# === Эндпоинты ===


@router.get(
    "/",
    response_model=IntegrationsResponse,
    summary="Список интеграций",
)
async def get_integrations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> IntegrationsResponse:
    """Получить список интеграций пользователя."""
    _require_enterprise(current_user)

    repo = MarketplaceKeyRepository(db)
    keys = await repo.get_all_for_user(current_user.id)

    # Формируем ответ
    integrations = []

    # Всегда показываем WB (подключён или нет)
    wb_key = next((k for k in keys if k.marketplace == "wb"), None)
    integrations.append(
        IntegrationInfo(
            marketplace="wb",
            connected=wb_key is not None,
            products_count=wb_key.products_count if wb_key else 0,
            connected_at=wb_key.connected_at if wb_key else None,
            last_synced_at=wb_key.last_synced_at if wb_key else None,
        )
    )

    return IntegrationsResponse(integrations=integrations)


@router.post(
    "/wb/connect",
    response_model=ConnectResponse,
    summary="Подключить Wildberries",
)
async def connect_wildberries(
    request: ConnectWBRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ConnectResponse:
    """
    Подключить Wildberries API.

    Проверяет валидность ключа и сохраняет зашифрованным.
    """
    _require_enterprise(current_user)

    # Валидируем ключ
    api = WildberriesAPI(request.api_key)
    if not await api.validate():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный API ключ Wildberries. Проверьте ключ и права доступа.",
        )

    # Получаем количество товаров
    try:
        products_count = await api.get_products_count()
    except WildberriesAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка WB API: {e}",
        )

    # Сохраняем ключ
    repo = MarketplaceKeyRepository(db)
    mk = await repo.create(current_user, "wb", request.api_key)
    await repo.update_sync_stats(mk, products_count)

    return ConnectResponse(
        success=True,
        message=f"Wildberries подключён. Найдено {products_count} товаров.",
        products_count=products_count,
    )


@router.post(
    "/wb/sync",
    response_model=SyncResponse,
    summary="Синхронизировать товары с WB",
)
async def sync_wildberries(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SyncResponse:
    """
    Синхронизировать товары с Wildberries.

    Загружает все товары и сохраняет в базу ProductCard.
    """
    _require_enterprise(current_user)

    # Получаем ключ
    mk_repo = MarketplaceKeyRepository(db)
    mk = await mk_repo.get_by_user_and_marketplace(current_user.id, "wb")

    if not mk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wildberries не подключён",
        )

    # Загружаем товары
    api_key = await mk_repo.get_decrypted_key(mk)
    api = WildberriesAPI(api_key)

    try:
        wb_products = await api.get_all_products()
    except WildberriesAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка синхронизации: {e}",
        )

    # Сохраняем в ProductCard
    product_repo = ProductRepository(db)
    new_count = 0

    for wp in wb_products:
        # Проверяем существует ли
        existing = await product_repo.get_by_barcode(current_user.id, wp.barcode)
        if existing:
            # Обновляем если нужно
            continue

        # Создаём новый
        await product_repo.create(
            user_id=current_user.id,
            barcode=wp.barcode,
            name=wp.name,
            article=wp.article,
            size=wp.size,
            color=wp.color,
            brand=wp.brand,
        )
        new_count += 1

    # Обновляем статистику
    await mk_repo.update_sync_stats(mk, len(wb_products))

    return SyncResponse(
        success=True,
        message="Синхронизация завершена",
        synced_count=len(wb_products),
        new_count=new_count,
    )


@router.delete(
    "/wb",
    response_model=MessageResponse,
    summary="Отключить Wildberries",
)
async def disconnect_wildberries(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Отключить интеграцию с Wildberries."""
    _require_enterprise(current_user)

    repo = MarketplaceKeyRepository(db)
    mk = await repo.get_by_user_and_marketplace(current_user.id, "wb")

    if not mk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wildberries не подключён",
        )

    await repo.deactivate(mk)

    return MessageResponse(message="Wildberries отключён")
