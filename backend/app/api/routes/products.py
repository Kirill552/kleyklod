"""
API эндпоинты для работы с карточками товаров.

Карточки товаров позволяют хранить информацию о товарах пользователя
для быстрой генерации этикеток с автозаполнением.

Ограничения по тарифам:
- FREE: база карточек недоступна (403)
- PRO: до 100 карточек
- ENTERPRISE: безлимит
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import ProductCard, User, UserPlan
from app.models.schemas import (
    ProductCardBulkResponse,
    ProductCardCreate,
    ProductCardListResponse,
    ProductCardResponse,
    ProductCardSerialUpdate,
)
from app.repositories.product_repo import ProductRepository

router = APIRouter(prefix="/api/v1/products", tags=["Products"])

# Лимиты карточек по тарифам
PLAN_LIMITS = {
    UserPlan.FREE: 0,  # Недоступно
    UserPlan.PRO: 100,
    UserPlan.ENTERPRISE: float("inf"),  # Безлимит
}


async def _get_product_repo(db: AsyncSession = Depends(get_db)) -> ProductRepository:
    """Dependency для получения ProductRepository."""
    return ProductRepository(db)


def _check_plan_access(user: User) -> None:
    """
    Проверяет доступ к базе карточек по тарифу.

    Raises:
        HTTPException: 403 если FREE план
    """
    if user.plan == UserPlan.FREE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="База карточек доступна только на тарифах Pro и Enterprise",
        )


async def _check_cards_limit(
    user: User,
    repo: ProductRepository,
    additional_count: int = 1,
) -> None:
    """
    Проверяет лимит карточек для PRO тарифа.

    Args:
        user: Текущий пользователь
        repo: Репозиторий карточек
        additional_count: Сколько карточек хотим добавить

    Raises:
        HTTPException: 403 если лимит превышен
    """
    if user.plan == UserPlan.ENTERPRISE:
        return  # Безлимит

    current_count = await repo.count(user.id)
    limit = PLAN_LIMITS.get(user.plan, 0)

    if current_count + additional_count > limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Превышен лимит карточек ({limit} для тарифа {user.plan.value}). "
            f"Текущее количество: {current_count}. "
            "Перейдите на тариф Enterprise для безлимитного хранения.",
        )


def _card_to_response(card: ProductCard) -> ProductCardResponse:
    """Преобразует модель ProductCard в Pydantic response."""
    return ProductCardResponse(
        id=card.id,
        barcode=card.barcode,
        name=card.name,
        article=card.article,
        size=card.size,
        color=card.color,
        composition=card.composition,
        country=card.country,
        brand=card.brand,
        last_serial_number=card.last_serial_number,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.get("", response_model=ProductCardListResponse)
async def list_products(
    search: str | None = Query(default=None, description="Поиск по баркоду, названию, артикулу"),
    limit: int = Query(default=100, ge=1, le=1000, description="Количество записей"),
    offset: int = Query(default=0, ge=0, description="Смещение для пагинации"),
    user: User = Depends(get_current_user),
    repo: ProductRepository = Depends(_get_product_repo),
) -> ProductCardListResponse:
    """
    Получить список карточек товаров пользователя.

    Параметры:
    - search: Поиск по баркоду, названию, артикулу или бренду (опционально)
    - limit: Количество записей (по умолчанию 100, максимум 1000)
    - offset: Смещение для пагинации

    Возвращает:
    - items: Список карточек
    - total: Общее количество карточек

    Ограничения по тарифам:
    - FREE: 403 Forbidden
    - PRO: до 100 карточек
    - ENTERPRISE: безлимит
    """
    # Проверяем доступ по тарифу
    _check_plan_access(user)

    # Получаем общее количество для пагинации
    total = await repo.count(user.id)

    # Получаем карточки
    if search:
        cards = await repo.search(user.id, search, limit=limit)
    else:
        cards = await repo.get_all(user.id, limit=limit, offset=offset)

    return ProductCardListResponse(
        items=[_card_to_response(card) for card in cards],
        total=total,
    )


@router.get("/{barcode}", response_model=ProductCardResponse)
async def get_product(
    barcode: str,
    user: User = Depends(get_current_user),
    repo: ProductRepository = Depends(_get_product_repo),
) -> ProductCardResponse:
    """
    Получить карточку товара по баркоду.

    Параметры:
    - barcode: EAN-13 или Code128 баркод

    Возвращает:
    - Карточка товара

    Ошибки:
    - 403: FREE план
    - 404: Карточка не найдена
    """
    # Проверяем доступ по тарифу
    _check_plan_access(user)

    card = await repo.get_by_barcode(user.id, barcode)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Карточка с баркодом {barcode} не найдена",
        )

    return _card_to_response(card)


@router.put("/{barcode}", response_model=ProductCardResponse)
async def upsert_product(
    barcode: str,
    data: ProductCardCreate,
    user: User = Depends(get_current_user),
    repo: ProductRepository = Depends(_get_product_repo),
) -> ProductCardResponse:
    """
    Создать или обновить карточку товара (upsert).

    Если карточка с таким баркодом уже существует — обновляет её.
    Если нет — создаёт новую.

    Параметры:
    - barcode: EAN-13 или Code128 баркод (в URL)
    - data: Данные карточки (в теле запроса)

    Возвращает:
    - Созданная или обновлённая карточка

    Ошибки:
    - 403: FREE план или превышен лимит карточек (PRO)
    - 422: Невалидные данные
    """
    # Проверяем доступ по тарифу
    _check_plan_access(user)

    # Проверяем что barcode в URL совпадает с barcode в теле
    if barcode != data.barcode:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Баркод в URL должен совпадать с баркодом в теле запроса",
        )

    # Проверяем существует ли уже карточка
    existing = await repo.get_by_barcode(user.id, barcode)
    if not existing:
        # Новая карточка — проверяем лимит
        await _check_cards_limit(user, repo, additional_count=1)

    # Upsert
    card = await repo.upsert(
        user_id=user.id,
        barcode=barcode,
        name=data.name,
        article=data.article,
        size=data.size,
        color=data.color,
        composition=data.composition,
        country=data.country,
        brand=data.brand,
    )

    return _card_to_response(card)


@router.post("/bulk", response_model=ProductCardBulkResponse)
async def bulk_upsert_products(
    items: list[ProductCardCreate],
    user: User = Depends(get_current_user),
    repo: ProductRepository = Depends(_get_product_repo),
) -> ProductCardBulkResponse:
    """
    Массовый upsert карточек товаров.

    Создаёт новые карточки и обновляет существующие в одном запросе.
    Полезно для импорта данных из Excel или синхронизации.

    Параметры:
    - items: Список карточек для создания/обновления

    Возвращает:
    - created: Количество созданных карточек
    - updated: Количество обновлённых карточек
    - skipped: Количество пропущенных (пустой barcode)

    Ограничения:
    - Максимум 1000 карточек за раз
    - PRO: до 100 карточек всего

    Ошибки:
    - 403: FREE план или превышен лимит
    - 422: Слишком много карточек в запросе
    """
    # Проверяем доступ по тарифу
    _check_plan_access(user)

    # Ограничение на размер batch
    if len(items) > 1000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Максимум 1000 карточек за раз",
        )

    # Считаем сколько новых карточек будет создано
    existing_barcodes = {
        card.barcode
        for card in await repo.get_by_barcodes(
            user.id,
            [item.barcode for item in items if item.barcode],
        )
    }
    new_count = sum(1 for item in items if item.barcode and item.barcode not in existing_barcodes)

    # Проверяем лимит
    if new_count > 0:
        await _check_cards_limit(user, repo, additional_count=new_count)

    # Выполняем bulk upsert
    result = await repo.bulk_upsert(
        user_id=user.id,
        items=[item.model_dump() for item in items],
    )

    return ProductCardBulkResponse(
        created=result["created"],
        updated=result["updated"],
        skipped=result["skipped"],
    )


@router.delete("/{barcode}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    barcode: str,
    user: User = Depends(get_current_user),
    repo: ProductRepository = Depends(_get_product_repo),
) -> None:
    """
    Удалить карточку товара.

    Параметры:
    - barcode: EAN-13 или Code128 баркод

    Возвращает:
    - 204 No Content при успехе

    Ошибки:
    - 403: FREE план
    - 404: Карточка не найдена
    """
    # Проверяем доступ по тарифу
    _check_plan_access(user)

    deleted = await repo.delete(user.id, barcode)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Карточка с баркодом {barcode} не найдена",
        )


@router.patch("/{barcode}/serial", response_model=ProductCardResponse)
async def update_serial_number(
    barcode: str,
    data: ProductCardSerialUpdate,
    user: User = Depends(get_current_user),
    repo: ProductRepository = Depends(_get_product_repo),
) -> ProductCardResponse:
    """
    Обновить последний серийный номер карточки.

    Используется при генерации нумерованных этикеток для сохранения
    последнего использованного номера и продолжения нумерации.

    Параметры:
    - barcode: EAN-13 или Code128 баркод
    - data: Новый серийный номер

    Возвращает:
    - Обновлённая карточка

    Ошибки:
    - 403: FREE план
    - 404: Карточка не найдена
    """
    # Проверяем доступ по тарифу
    _check_plan_access(user)

    card = await repo.get_by_barcode(user.id, barcode)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Карточка с баркодом {barcode} не найдена",
        )

    await repo.update_serial(user.id, barcode, data.last_serial_number)

    # Получаем обновлённую карточку
    card = await repo.get_by_barcode(user.id, barcode)
    return _card_to_response(card)  # type: ignore
