"""
API эндпоинты для работы с платежами через ЮКассу.

Создание платежей, webhook обработка, история платежей.
"""

import ipaddress
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, verify_bot_secret
from app.db.database import get_db
from app.db.models import User, UserPlan
from app.models.schemas import PaymentHistoryItem, PaymentPlan
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.services.yookassa_service import YooKassaService

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])
logger = logging.getLogger(__name__)


# === Защита webhook от подделки (IP Whitelist ЮКассы) ===

YOOKASSA_IP_WHITELIST: list[ipaddress.IPv4Network | ipaddress.IPv4Address] = [
    ipaddress.ip_network("185.71.76.0/27"),
    ipaddress.ip_network("185.71.77.0/27"),
    ipaddress.ip_network("77.75.153.0/25"),
    ipaddress.ip_network("77.75.154.128/25"),
    ipaddress.ip_address("77.75.156.11"),
    ipaddress.ip_address("77.75.156.35"),
]


def is_yookassa_ip(client_ip: str) -> bool:
    """Проверяет, что IP адрес принадлежит ЮКассе."""
    try:
        ip = ipaddress.ip_address(client_ip)
        for allowed in YOOKASSA_IP_WHITELIST:
            if isinstance(allowed, ipaddress.IPv4Network):
                if ip in allowed:
                    return True
            elif ip == allowed:
                return True
        return False
    except ValueError:
        return False


# === Тарифы ===

PLANS = {
    "pro": {"price_rub": 490, "duration_days": 30},
    "enterprise": {"price_rub": 1990, "duration_days": 30},
}

# Список доступных тарифов для отображения
AVAILABLE_PLANS: list[PaymentPlan] = [
    PaymentPlan(
        id="free",
        name="Free",
        price_rub=0,
        period="month",
        features=[
            "50 этикеток в день",
            "Базовая проверка качества",
            "Поддержка в чате",
        ],
    ),
    PaymentPlan(
        id="pro",
        name="Pro",
        price_rub=490,
        period="month",
        features=[
            "500 этикеток в день",
            "Расширенная проверка качества",
            "Приоритетная поддержка",
            "История генераций",
        ],
    ),
    PaymentPlan(
        id="enterprise",
        name="Enterprise",
        price_rub=1990,
        period="month",
        features=[
            "Безлимитные этикетки",
            "API доступ",
            "Персональный менеджер",
            "SLA 99.9%",
        ],
    ),
]


# === Pydantic модели ===


class CreatePaymentRequest(BaseModel):
    """Запрос на создание платежа."""

    plan: str = Field(description="Тариф (pro/enterprise)")
    telegram_id: int | None = Field(default=None, description="Telegram ID (опционально)")
    vk_user_id: int | None = Field(default=None, description="VK User ID (для VK Mini App)")


class CreatePaymentResponse(BaseModel):
    """Ответ с данными платежа."""

    payment_id: str = Field(description="ID платежа в нашей системе")
    confirmation_url: str = Field(description="URL для оплаты в ЮКассе")
    amount: int = Field(description="Сумма платежа в рублях")
    currency: str = Field(default="RUB", description="Валюта")


# === Endpoints ===


@router.post("/create")
async def create_payment(
    request: CreatePaymentRequest,
    db: AsyncSession = Depends(get_db),
) -> CreatePaymentResponse:
    """
    Создать платёж в ЮКассе.

    1. Проверяет валидность тарифа
    2. Создаёт платёж в ЮКассе
    3. Сохраняет платёж в БД со статусом PENDING
    4. Возвращает URL для оплаты
    """
    # Валидация тарифа
    if request.plan not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тариф. Доступны: {', '.join(PLANS.keys())}",
        )

    plan_config = PLANS[request.plan]
    amount = plan_config["price_rub"]

    # Создаём платёж в ЮКассе
    yookassa = YooKassaService()

    # Определяем источник платежа
    if request.vk_user_id:
        source = "vk_mini_app"
    elif request.telegram_id:
        source = "bot"
    else:
        source = "web"

    try:
        payment_data = await yookassa.create_payment(
            amount=amount,
            plan=request.plan,
            telegram_id=request.telegram_id,
            vk_user_id=request.vk_user_id,
            source=source,
        )
    except Exception as e:
        logger.error(f"Ошибка создания платежа в ЮКассе: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать платёж. Попробуйте позже.",
        ) from e

    # Находим пользователя по telegram_id или vk_user_id
    user_id = None
    user_repo = UserRepository(db)

    if request.telegram_id:
        user = await user_repo.get_by_telegram_id(request.telegram_id)
        if user:
            user_id = user.id

    if not user_id and request.vk_user_id:
        user = await user_repo.get_by_vk_id(request.vk_user_id)
        if user:
            user_id = user.id

    # Если user_id не найден, создаём платёж без привязки к пользователю
    # (пользователь будет привязан при webhook, если передан telegram_id/vk_user_id в metadata)
    if not user_id and not request.telegram_id and not request.vk_user_id:
        logger.warning("Платёж создан без привязки к пользователю")

    # Сохраняем платёж в БД только если есть user_id
    # Если нет - платёж создастся при webhook
    payment_id_for_response = payment_data["payment_id"]

    if user_id:
        payment_repo = PaymentRepository(db)

        try:
            # Определяем plan enum
            plan_enum = UserPlan.PRO if request.plan == "pro" else UserPlan.ENTERPRISE

            payment = await payment_repo.create(
                user_id=user_id,
                amount=amount,
                currency="RUB",
                provider="yookassa",
                plan=plan_enum,
                external_id=payment_data["payment_id"],
            )
            await db.commit()

            logger.info(f"Платёж {payment.id} создан для тарифа {request.plan}")
            payment_id_for_response = str(payment.id)

        except Exception as e:
            logger.error(f"Ошибка сохранения платежа в БД: {e}")
            await db.rollback()
            # Не падаем - платёж в ЮКассе создан, сохраним при webhook
            logger.warning("Платёж сохранится при webhook")
    else:
        logger.info(
            f"Платёж {payment_data['payment_id']} создан без user_id, сохранится при webhook"
        )

    return CreatePaymentResponse(
        payment_id=payment_id_for_response,
        confirmation_url=payment_data["confirmation_url"],
        amount=amount,
        currency="RUB",
    )


@router.post("/webhook")
async def yookassa_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Webhook от ЮКассы для обработки статуса платежей.

    События:
    - payment.succeeded: платёж успешен → активируем подписку
    - payment.canceled: платёж отменён → помечаем как FAILED

    Всегда возвращает HTTP 200 {"status": "ok"} для подтверждения получения.
    """
    # Проверка IP адреса отправителя (защита от подделки webhook)
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else ""

    if not is_yookassa_ip(client_ip):
        logger.warning(f"Webhook от неизвестного IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized webhook source",
        )

    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Ошибка парсинга webhook: {e}")
        # Возвращаем 200 чтобы ЮКасса не повторяла запрос
        return {"status": "error", "message": "Invalid JSON"}

    event = body.get("event")
    payment_obj = body.get("object", {})
    payment_id = payment_obj.get("id")

    logger.info(f"Получен webhook от ЮКассы: event={event}, payment_id={payment_id}")

    # Репозитории
    payment_repo = PaymentRepository(db)
    user_repo = UserRepository(db)

    # Обработка события payment.succeeded
    if event == "payment.succeeded":
        try:
            # Получаем metadata
            metadata = payment_obj.get("metadata", {})
            user_id_str = metadata.get("user_id")
            telegram_id_str = metadata.get("telegram_id")
            vk_user_id_str = metadata.get("vk_user_id")
            plan = metadata.get("plan")

            logger.info(
                f"Платёж успешен: user_id={user_id_str}, telegram_id={telegram_id_str}, "
                f"vk_user_id={vk_user_id_str}, plan={plan}"
            )

            # Находим пользователя
            user = None

            # Сначала пытаемся найти по user_id
            if user_id_str:
                try:
                    user = await user_repo.get_by_id(UUID(user_id_str))
                except Exception as e:
                    logger.warning(f"Ошибка поиска пользователя по user_id {user_id_str}: {e}")

            # Если не нашли, пытаемся найти по telegram_id
            if not user and telegram_id_str:
                try:
                    telegram_id = int(telegram_id_str)
                    user = await user_repo.get_by_telegram_id(telegram_id)
                except Exception as e:
                    logger.warning(
                        f"Ошибка поиска пользователя по telegram_id {telegram_id_str}: {e}"
                    )

            # Если не нашли, пытаемся найти по vk_user_id
            if not user and vk_user_id_str:
                try:
                    vk_user_id = int(vk_user_id_str)
                    user = await user_repo.get_by_vk_id(vk_user_id)
                except Exception as e:
                    logger.warning(
                        f"Ошибка поиска пользователя по vk_user_id {vk_user_id_str}: {e}"
                    )

            if not user:
                logger.error(
                    f"Пользователь не найден для платежа {payment_id}. "
                    f"user_id={user_id_str}, telegram_id={telegram_id_str}, vk_user_id={vk_user_id_str}"
                )
                return {"status": "ok", "message": "Payment completed but user not found"}

            # Находим платёж в БД
            payment = await payment_repo.get_by_external_id(payment_id)

            # Если платёж не найден - создаём его (был создан без user_id)
            if not payment:
                logger.info(f"Платёж {payment_id} не найден в БД, создаём...")
                amount_value = payment_obj.get("amount", {}).get("value", "0")
                plan_enum = UserPlan.PRO if plan == "pro" else UserPlan.ENTERPRISE

                payment = await payment_repo.create(
                    user_id=user.id,
                    amount=int(float(amount_value)),
                    currency="RUB",
                    provider="yookassa",
                    plan=plan_enum,
                    external_id=payment_id,
                )
                logger.info(f"Платёж {payment.id} создан при webhook")

            # Определяем длительность подписки
            duration = PLANS.get(plan, {}).get("duration_days", 30)

            # Активируем подписку
            await payment_repo.activate_subscription(user, payment, duration)
            await db.commit()

            logger.info(
                f"Подписка активирована для пользователя {user.id}, план {plan}, "
                f"истекает {user.plan_expires_at}"
            )

        except Exception as e:
            logger.error(f"Ошибка обработки payment.succeeded: {e}", exc_info=True)
            await db.rollback()
            # Возвращаем 200 чтобы ЮКасса не повторяла запрос
            return {"status": "error", "message": str(e)}

    # Обработка события payment.canceled
    elif event == "payment.canceled":
        try:
            # Находим платёж в БД
            payment = await payment_repo.get_by_external_id(payment_id)

            if payment:
                await payment_repo.fail(payment)
                await db.commit()
                logger.info(f"Платёж {payment_id} отменён")
            else:
                logger.warning(f"Платёж {payment_id} не найден в БД для отмены")

        except Exception as e:
            logger.error(f"Ошибка обработки payment.canceled: {e}", exc_info=True)
            await db.rollback()
            return {"status": "error", "message": str(e)}

    else:
        logger.info(f"Игнорируем событие {event}")

    return {"status": "ok"}


@router.get("/plans")
async def get_plans() -> list[PaymentPlan]:
    """
    Получить список доступных тарифных планов.

    Возвращает Free, Pro и Enterprise с ценами в рублях.
    """
    return AVAILABLE_PLANS


@router.get("/history")
async def get_my_payment_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PaymentHistoryItem]:
    """
    Получить историю платежей текущего пользователя (JWT auth).

    Используется frontend для отображения истории платежей.

    Returns:
        Список платежей отсортированный по дате (новые сверху)
    """
    payment_repo = PaymentRepository(db)
    payments = await payment_repo.get_user_payments(user.id, limit=50)

    return [
        PaymentHistoryItem(
            id=str(p.id),
            plan=p.plan.value if p.plan else "unknown",
            amount=p.amount,
            currency=p.currency,
            status=p.status.value,
            created_at=p.created_at.isoformat(),
        )
        for p in payments
    ]


@router.get("/{telegram_id}/history", dependencies=[Depends(verify_bot_secret)])
async def get_payment_history(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[PaymentHistoryItem]:
    """
    Получить историю платежей пользователя.

    Args:
        telegram_id: Telegram ID пользователя

    Returns:
        Список платежей отсортированный по дате (новые сверху)
    """
    # Находим пользователя
    user_repo = UserRepository(db)
    user = await user_repo.get_by_telegram_id(telegram_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    # Получаем платежи
    payment_repo = PaymentRepository(db)
    payments = await payment_repo.get_user_payments(user.id, limit=50)

    # Конвертируем в PaymentHistoryItem
    history = [
        PaymentHistoryItem(
            id=str(p.id),
            plan=p.plan.value if p.plan else "unknown",
            amount=p.amount,
            currency=p.currency,
            status=p.status.value,
            created_at=p.created_at.isoformat(),
        )
        for p in payments
    ]

    return history
