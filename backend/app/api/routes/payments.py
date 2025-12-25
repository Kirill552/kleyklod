"""
API эндпоинты для работы с платежами.

Активация подписок, история платежей, тарифы.
"""

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    PaymentPlan,
    PaymentActivateRequest,
    PaymentActivateResponse,
    PaymentHistoryItem,
)

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])

# Временное хранилище платежей (пока нет БД)
_payments_db: dict[str, dict] = {}

# Ссылка на хранилище пользователей из users.py
# В продакшене — использовать общий репозиторий
from app.api.routes.users import _users_db


# Тарифные планы
AVAILABLE_PLANS: list[PaymentPlan] = [
    PaymentPlan(
        id="free",
        name="Free",
        price_rub=0,
        price_stars=None,
        period="month",
        features=[
            "50 этикеток в день",
            "Базовый Pre-flight",
            "Поддержка в чате",
        ],
    ),
    PaymentPlan(
        id="pro",
        name="Pro",
        price_rub=490,
        price_stars=377,
        period="month",
        features=[
            "500 этикеток в день",
            "Расширенный Pre-flight",
            "Приоритетная поддержка",
            "История генераций",
        ],
    ),
    PaymentPlan(
        id="enterprise",
        name="Enterprise",
        price_rub=1990,
        price_stars=1531,
        period="month",
        features=[
            "Безлимитные этикетки",
            "API доступ",
            "Персональный менеджер",
            "SLA 99.9%",
        ],
    ),
]


@router.get("/plans")
async def get_plans() -> list[PaymentPlan]:
    """
    Получить список доступных тарифных планов.
    """
    return AVAILABLE_PLANS


@router.post("/activate")
async def activate_subscription(request: PaymentActivateRequest) -> PaymentActivateResponse:
    """
    Активировать подписку после успешной оплаты через Telegram Stars.

    Вызывается ботом после получения successful_payment.
    """
    telegram_id = request.telegram_id

    # Проверяем существование пользователя
    if telegram_id not in _users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден. Сначала зарегистрируйтесь.",
        )

    # Валидация плана
    if request.plan not in ("pro", "enterprise"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимый тариф. Доступны: pro, enterprise",
        )

    # Создаём запись о платеже
    payment_id = str(uuid4())
    now = datetime.now()
    expires_at = now + timedelta(days=request.duration_days)

    payment = {
        "id": payment_id,
        "user_telegram_id": telegram_id,
        "plan": request.plan,
        "amount": request.total_amount,
        "currency": "XTR",  # Telegram Stars
        "status": "completed",
        "telegram_payment_charge_id": request.telegram_payment_charge_id,
        "provider_payment_charge_id": request.provider_payment_charge_id,
        "created_at": now.isoformat(),
    }
    _payments_db[payment_id] = payment

    # Обновляем подписку пользователя
    user = _users_db[telegram_id]
    user["plan"] = request.plan
    user["plan_expires_at"] = expires_at.isoformat()
    user["updated_at"] = now.isoformat()

    return PaymentActivateResponse(
        success=True,
        message=f"Подписка {request.plan.title()} активирована на {request.duration_days} дней",
        expires_at=expires_at.isoformat(),
    )


@router.get("/{telegram_id}/history")
async def get_payment_history(telegram_id: int) -> list[PaymentHistoryItem]:
    """
    Получить историю платежей пользователя.
    """
    if telegram_id not in _users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    # Фильтруем платежи этого пользователя
    user_payments = [
        PaymentHistoryItem(
            id=p["id"],
            plan=p["plan"],
            amount=p["amount"],
            currency=p["currency"],
            status=p["status"],
            created_at=p["created_at"],
        )
        for p in _payments_db.values()
        if p["user_telegram_id"] == telegram_id
    ]

    # Сортируем по дате (новые сверху)
    user_payments.sort(key=lambda x: x.created_at, reverse=True)

    return user_payments


@router.post("/webhook")
async def payment_webhook(payload: dict) -> dict:
    """
    Webhook для внешних платёжных систем (YooKassa и т.д.).

    В данной версии используется только Telegram Stars,
    поэтому этот endpoint — заглушка на будущее.
    """
    # TODO: Реализовать обработку webhooks от YooKassa
    return {"status": "ok", "message": "Webhook received"}
