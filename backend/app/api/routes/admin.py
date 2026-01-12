"""
API эндпоинты для администрирования.

Защищены X-Bot-Secret — доступны только для ботов.
"""

import hmac
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_db
from app.db.models import Payment, PaymentStatus, UsageLog, User, UserPlan

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


class SourceStats(BaseModel):
    """Статистика по источникам регистрации."""

    vk: int
    vk_percent: float
    telegram: int
    telegram_percent: float
    site: int
    site_percent: float


class UsersStats(BaseModel):
    """Статистика по пользователям."""

    total: int
    trial_active: int
    pro: int
    enterprise: int


class GenerationsStats(BaseModel):
    """Статистика по генерациям."""

    today: int
    yesterday: int
    month: int
    total: int


class PaymentsStats(BaseModel):
    """Статистика по платежам."""

    month_amount: int  # в копейках
    month_count: int


class AdminStatsResponse(BaseModel):
    """Ответ со статистикой для админа."""

    users: UsersStats
    sources: SourceStats
    generations: GenerationsStats
    payments: PaymentsStats


def verify_bot_secret(x_bot_secret: str | None = Header(None, alias="X-Bot-Secret")) -> None:
    """Проверка секрета бота."""
    settings = get_settings()
    if not x_bot_secret or not hmac.compare_digest(x_bot_secret, settings.bot_secret_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный секрет бота",
        )


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Статистика проекта",
    description="Агрегированная статистика для админа. Защищено X-Bot-Secret.",
    include_in_schema=False,  # Скрыт из Swagger
)
async def get_admin_stats(
    _: None = Depends(verify_bot_secret),
    db: AsyncSession = Depends(get_db),
) -> AdminStatsResponse:
    """
    Получить агрегированную статистику проекта.

    Включает:
    - Пользователи: всего, trial, PRO, Enterprise
    - Источники регистрации: VK, Telegram, сайт (с процентами)
    - Генерации: сегодня, вчера, за месяц, всего
    - Платежи: сумма и количество за месяц
    """
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # === Пользователи ===
    # Всего
    total_users = await db.scalar(select(func.count()).select_from(User))

    # С активным Trial (free + trial_ends_at > now)
    trial_active = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(
            and_(
                User.plan == UserPlan.FREE,
                User.trial_ends_at > now,
            )
        )
    )

    # PRO
    pro_users = await db.scalar(
        select(func.count()).select_from(User).where(User.plan == UserPlan.PRO)
    )

    # Enterprise
    enterprise_users = await db.scalar(
        select(func.count()).select_from(User).where(User.plan == UserPlan.ENTERPRISE)
    )

    # === Источники регистрации ===
    # Из VK (vk_user_id_hash IS NOT NULL)
    from_vk = await db.scalar(
        select(func.count()).select_from(User).where(User.vk_user_id_hash.isnot(None))
    )

    # Из Telegram (telegram_id_hash IS NOT NULL AND vk_user_id_hash IS NULL)
    # Примечание: если у пользователя оба — считаем как VK (первичный)
    from_telegram = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(
            and_(
                User.telegram_id_hash.isnot(None),
                User.vk_user_id_hash.is_(None),
            )
        )
    )

    # Только сайт (оба NULL)
    from_site = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(
            and_(
                User.vk_user_id_hash.is_(None),
                User.telegram_id_hash.is_(None),
            )
        )
    )

    # Проценты
    total = total_users or 1  # Защита от деления на 0
    vk_percent = round((from_vk or 0) / total * 100, 1)
    telegram_percent = round((from_telegram or 0) / total * 100, 1)
    site_percent = round((from_site or 0) / total * 100, 1)

    # === Генерации ===
    # Сегодня
    gen_today = await db.scalar(
        select(func.coalesce(func.sum(UsageLog.labels_count), 0)).where(
            UsageLog.created_at >= today_start
        )
    )

    # Вчера
    gen_yesterday = await db.scalar(
        select(func.coalesce(func.sum(UsageLog.labels_count), 0)).where(
            and_(
                UsageLog.created_at >= yesterday_start,
                UsageLog.created_at < today_start,
            )
        )
    )

    # За месяц
    gen_month = await db.scalar(
        select(func.coalesce(func.sum(UsageLog.labels_count), 0)).where(
            UsageLog.created_at >= month_start
        )
    )

    # Всего
    gen_total = await db.scalar(select(func.coalesce(func.sum(UsageLog.labels_count), 0)))

    # === Платежи ===
    # За месяц (успешные)
    payments_month = await db.execute(
        select(
            func.coalesce(func.sum(Payment.amount), 0),
            func.count(),
        ).where(
            and_(
                Payment.status == PaymentStatus.SUCCESS,
                Payment.created_at >= month_start,
            )
        )
    )
    payments_row = payments_month.one()
    month_amount = payments_row[0] or 0
    month_count = payments_row[1] or 0

    return AdminStatsResponse(
        users=UsersStats(
            total=total_users or 0,
            trial_active=trial_active or 0,
            pro=pro_users or 0,
            enterprise=enterprise_users or 0,
        ),
        sources=SourceStats(
            vk=from_vk or 0,
            vk_percent=vk_percent,
            telegram=from_telegram or 0,
            telegram_percent=telegram_percent,
            site=from_site or 0,
            site_percent=site_percent,
        ),
        generations=GenerationsStats(
            today=gen_today or 0,
            yesterday=gen_yesterday or 0,
            month=gen_month or 0,
            total=gen_total or 0,
        ),
        payments=PaymentsStats(
            month_amount=month_amount,
            month_count=month_count,
        ),
    )
