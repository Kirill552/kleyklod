"""
API эндпоинты для работы с пользователями.

Регистрация, профиль, статистика использования.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, verify_bot_secret
from app.config import get_settings
from app.db.database import get_db
from app.db.models import User
from app.models.schemas import (
    PaymentHistoryItem,
    UserLabelPreferences,
    UserLabelPreferencesUpdate,
    UserProfileResponse,
    UserRegisterRequest,
    UserResponse,
    UserStatsResponse,
)
from app.repositories import PaymentRepository, UsageRepository, UserRepository

router = APIRouter(prefix="/api/v1/users", tags=["Users"])
settings = get_settings()

# Временное in-memory хранилище для обратной совместимости
# Используется когда БД недоступна (разработка без Docker)
_users_db: dict[int, dict] = {}
_usage_db: dict[int, dict] = {}


async def _get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency для получения UserRepository."""
    return UserRepository(db)


async def _get_usage_repo(db: AsyncSession = Depends(get_db)) -> UsageRepository:
    """Dependency для получения UsageRepository."""
    return UsageRepository(db)


async def _get_payment_repo(db: AsyncSession = Depends(get_db)) -> PaymentRepository:
    """Dependency для получения PaymentRepository."""
    return PaymentRepository(db)


# === Эндпоинты для текущего пользователя (JWT авторизация) ===


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """
    Получить данные текущего пользователя по JWT токену.

    Используется фронтендом для отображения профиля.
    """
    return UserResponse(
        id=user.id,
        telegram_id=int(user.telegram_id) if user.telegram_id else None,
        username=user.telegram_username,
        first_name=user.first_name,
        photo_url=user.photo_url,
        plan=user.plan,
        plan_expires_at=user.plan_expires_at,
        created_at=user.created_at,
    )


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
    user: User = Depends(get_current_user),
    usage_repo: UsageRepository = Depends(_get_usage_repo),
) -> UserStatsResponse:
    """
    Получить статистику использования текущего пользователя.

    Возвращает:
    - today_used: использовано сегодня
    - today_limit: дневной лимит по тарифу
    - total_generated: всего сгенерировано за всё время
    - this_month: сгенерировано за текущий месяц
    """
    # Получаем статистику
    stats = await usage_repo.get_usage_stats(user.id)
    this_month = await usage_repo.get_monthly_usage(user.id)

    # Определяем лимит по тарифу
    if user.plan.value == "free":
        daily_limit = settings.free_tier_daily_limit
    elif user.plan.value == "pro":
        daily_limit = 500
    else:
        daily_limit = 999999

    return UserStatsResponse(
        today_used=stats["today_generated"],
        today_limit=daily_limit,
        total_generated=stats["total_generated"],
        this_month=this_month,
    )


@router.get("/me/preferences", response_model=UserLabelPreferences)
async def get_my_preferences(
    user: User = Depends(get_current_user),
) -> UserLabelPreferences:
    """
    Получить настройки генерации этикеток текущего пользователя.

    Возвращает сохранённые предпочтения: организацию, layout, размер и т.д.
    """
    return UserLabelPreferences(
        organization_name=user.organization_name,
        preferred_layout=user.preferred_layout or "classic",
        preferred_label_size=user.preferred_label_size or "58x40",
        preferred_format=user.preferred_format or "combined",
        show_article=user.show_article if user.show_article is not None else True,
        show_size_color=user.show_size_color if user.show_size_color is not None else True,
        show_name=user.show_name if user.show_name is not None else True,
    )


@router.put("/me/preferences", response_model=UserLabelPreferences)
async def update_my_preferences(
    update_data: UserLabelPreferencesUpdate,
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(_get_user_repo),
) -> UserLabelPreferences:
    """
    Обновить настройки генерации этикеток текущего пользователя.

    Обновляются только переданные поля (partial update).
    """
    # Собираем поля для обновления (только те, что переданы)
    update_fields = {}
    if update_data.organization_name is not None:
        update_fields["organization_name"] = update_data.organization_name
    if update_data.preferred_layout is not None:
        update_fields["preferred_layout"] = update_data.preferred_layout
    if update_data.preferred_label_size is not None:
        update_fields["preferred_label_size"] = update_data.preferred_label_size
    if update_data.preferred_format is not None:
        update_fields["preferred_format"] = update_data.preferred_format
    if update_data.show_article is not None:
        update_fields["show_article"] = update_data.show_article
    if update_data.show_size_color is not None:
        update_fields["show_size_color"] = update_data.show_size_color
    if update_data.show_name is not None:
        update_fields["show_name"] = update_data.show_name

    # Обновляем пользователя
    if update_fields:
        await user_repo.update_preferences(user, update_fields)

    # Возвращаем обновлённые настройки
    return UserLabelPreferences(
        organization_name=update_fields.get("organization_name", user.organization_name),
        preferred_layout=update_fields.get("preferred_layout", user.preferred_layout) or "classic",
        preferred_label_size=update_fields.get("preferred_label_size", user.preferred_label_size)
        or "58x40",
        preferred_format=update_fields.get("preferred_format", user.preferred_format) or "combined",
        show_article=update_fields.get(
            "show_article", user.show_article if user.show_article is not None else True
        ),
        show_size_color=update_fields.get(
            "show_size_color", user.show_size_color if user.show_size_color is not None else True
        ),
        show_name=update_fields.get(
            "show_name", user.show_name if user.show_name is not None else True
        ),
    )


# === Эндпоинты для бота (по telegram_id) ===


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegisterRequest,
    user_repo: UserRepository = Depends(_get_user_repo),
) -> dict:
    """
    Регистрация нового пользователя или обновление существующего.

    Вызывается автоматически при первом обращении к боту.
    """
    try:
        user, is_new = await user_repo.get_or_create(
            telegram_id=request.telegram_id,
            username=request.username,
            first_name=request.first_name,
            last_name=request.last_name,
        )

        if not is_new:
            # Обновляем данные существующего пользователя
            await user_repo.update_profile(
                user=user,
                username=request.username,
                first_name=request.first_name,
                last_name=request.last_name,
            )

        return {
            "success": True,
            "message": "Пользователь зарегистрирован" if is_new else "Пользователь обновлён",
            "user_id": str(user.id),
            "is_new": is_new,
        }

    except Exception:
        # Fallback на in-memory хранилище при ошибке БД
        return await _register_user_fallback(request)


async def _register_user_fallback(request: UserRegisterRequest) -> dict:
    """Fallback регистрация без БД."""
    from datetime import datetime
    from uuid import uuid4

    telegram_id = request.telegram_id

    if telegram_id in _users_db:
        user = _users_db[telegram_id]
        user["username"] = request.username
        user["first_name"] = request.first_name
        user["last_name"] = request.last_name
        user["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "message": "Пользователь обновлён",
            "user_id": user["id"],
            "is_new": False,
        }

    user_id = str(uuid4())
    now = datetime.now()

    _users_db[telegram_id] = {
        "id": user_id,
        "telegram_id": telegram_id,
        "username": request.username,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "plan": "free",
        "plan_expires_at": None,
        "consent_given_at": now.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    _usage_db[telegram_id] = {
        "total_generated": 0,
        "success_count": 0,
        "preflight_errors": 0,
        "daily_usage": {},
    }

    return {
        "success": True,
        "message": "Пользователь зарегистрирован",
        "user_id": user_id,
        "is_new": True,
    }


@router.get("/{telegram_id}/profile", dependencies=[Depends(verify_bot_secret)])
async def get_user_profile(
    telegram_id: int,
    user_repo: UserRepository = Depends(_get_user_repo),
    usage_repo: UsageRepository = Depends(_get_usage_repo),
) -> UserProfileResponse:
    """
    Получить профиль пользователя с статистикой.

    Возвращает план, лимиты и статистику использования.
    """
    try:
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        # Получаем статистику
        stats = await usage_repo.get_usage_stats(user.id)

        # Определение лимита по тарифу
        if user.plan.value == "free":
            daily_limit = settings.free_tier_daily_limit
        elif user.plan.value == "pro":
            daily_limit = 500
        else:
            daily_limit = 999999

        return UserProfileResponse(
            plan=user.plan.value,
            used_today=stats["today_generated"],
            daily_limit=daily_limit,
            total_generated=stats["total_generated"],
            success_count=stats["success_count"],
            preflight_errors=stats["error_count"],
            registered_at=user.created_at.isoformat() if user.created_at else "",
            subscription_expires_at=(
                user.plan_expires_at.isoformat() if user.plan_expires_at else None
            ),
        )

    except HTTPException:
        raise
    except Exception:
        # Fallback на in-memory
        return await _get_profile_fallback(telegram_id)


async def _get_profile_fallback(telegram_id: int) -> UserProfileResponse:
    """Fallback получение профиля без БД."""
    if telegram_id not in _users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    user = _users_db[telegram_id]
    usage = _usage_db.get(telegram_id, {})

    today = date.today().isoformat()
    daily_usage = usage.get("daily_usage", {})
    used_today = daily_usage.get(today, 0)

    plan = user.get("plan", "free")
    if plan == "free":
        daily_limit = settings.free_tier_daily_limit
    elif plan == "pro":
        daily_limit = 500
    else:
        daily_limit = 999999

    return UserProfileResponse(
        plan=plan,
        used_today=used_today,
        daily_limit=daily_limit,
        total_generated=usage.get("total_generated", 0),
        success_count=usage.get("success_count", 0),
        preflight_errors=usage.get("preflight_errors", 0),
        registered_at=user.get("created_at", ""),
        subscription_expires_at=user.get("plan_expires_at"),
    )


@router.get("/{telegram_id}/payments", dependencies=[Depends(verify_bot_secret)])
async def get_payment_history(
    telegram_id: int,
    user_repo: UserRepository = Depends(_get_user_repo),
    payment_repo: PaymentRepository = Depends(_get_payment_repo),
) -> list[PaymentHistoryItem]:
    """
    Получить историю платежей пользователя.
    """
    try:
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        payments = await payment_repo.get_completed_payments(user.id)

        return [
            PaymentHistoryItem(
                amount=p.amount,
                currency=p.currency,
                plan=p.plan.value if p.plan else "unknown",
                status=p.status.value,
                created_at=p.created_at.isoformat(),
            )
            for p in payments
        ]

    except HTTPException:
        raise
    except Exception:
        # БД недоступна — возвращаем пустой список
        return []


@router.post("/{telegram_id}/usage", dependencies=[Depends(verify_bot_secret)])
async def record_usage(
    telegram_id: int,
    labels_count: int,
    preflight_ok: bool = True,
    user_repo: UserRepository = Depends(_get_user_repo),
    usage_repo: UsageRepository = Depends(_get_usage_repo),
) -> dict:
    """
    Записать использование (внутренний endpoint).

    Вызывается после генерации этикеток.
    """
    try:
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        preflight_status = "ok" if preflight_ok else "error"
        await usage_repo.record_usage(
            user_id=user.id,
            labels_count=labels_count,
            preflight_status=preflight_status,
        )

        today_usage = await usage_repo.get_daily_usage(user.id)

        return {
            "success": True,
            "today_total": today_usage,
        }

    except HTTPException:
        raise
    except Exception:
        # Fallback на in-memory
        return await _record_usage_fallback(telegram_id, labels_count, preflight_ok)


async def _record_usage_fallback(
    telegram_id: int,
    labels_count: int,
    preflight_ok: bool,
) -> dict:
    """Fallback запись использования без БД."""
    if telegram_id not in _users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if telegram_id not in _usage_db:
        _usage_db[telegram_id] = {
            "total_generated": 0,
            "success_count": 0,
            "preflight_errors": 0,
            "daily_usage": {},
        }

    usage = _usage_db[telegram_id]
    today = date.today().isoformat()

    usage["total_generated"] += labels_count
    if preflight_ok:
        usage["success_count"] += 1
    else:
        usage["preflight_errors"] += 1

    if "daily_usage" not in usage:
        usage["daily_usage"] = {}
    usage["daily_usage"][today] = usage["daily_usage"].get(today, 0) + labels_count

    return {
        "success": True,
        "today_total": usage["daily_usage"][today],
    }


@router.get("/{telegram_id}/check-limit", dependencies=[Depends(verify_bot_secret)])
async def check_limit(
    telegram_id: int,
    labels_count: int = 1,
    user_repo: UserRepository = Depends(_get_user_repo),
    usage_repo: UsageRepository = Depends(_get_usage_repo),
) -> dict:
    """
    Проверить, не превышен ли лимит пользователя.
    """
    try:
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            # Новый пользователь — разрешаем Free лимит
            return {
                "allowed": labels_count <= settings.free_tier_daily_limit,
                "remaining": settings.free_tier_daily_limit - labels_count,
                "plan": "free",
                "used_today": 0,
                "daily_limit": settings.free_tier_daily_limit,
            }

        result = await usage_repo.check_limit(
            user=user,
            labels_count=labels_count,
            free_limit=settings.free_tier_daily_limit,
            pro_limit=500,
        )
        return result

    except Exception:
        # Fallback на in-memory
        return await _check_limit_fallback(telegram_id, labels_count)


async def _check_limit_fallback(telegram_id: int, labels_count: int) -> dict:
    """Fallback проверка лимита без БД."""
    if telegram_id not in _users_db:
        return {
            "allowed": labels_count <= settings.free_tier_daily_limit,
            "remaining": settings.free_tier_daily_limit - labels_count,
            "plan": "free",
            "used_today": 0,
            "daily_limit": settings.free_tier_daily_limit,
        }

    user = _users_db[telegram_id]
    usage = _usage_db.get(telegram_id, {})

    plan = user.get("plan", "free")
    today = date.today().isoformat()
    used_today = usage.get("daily_usage", {}).get(today, 0)

    if plan == "free":
        daily_limit = settings.free_tier_daily_limit
    elif plan == "pro":
        daily_limit = 500
    else:
        daily_limit = 999999

    remaining = daily_limit - used_today
    allowed = remaining >= labels_count

    return {
        "allowed": allowed,
        "remaining": remaining,
        "plan": plan,
        "used_today": used_today,
        "daily_limit": daily_limit,
    }
