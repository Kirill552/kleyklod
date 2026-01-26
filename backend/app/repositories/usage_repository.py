"""
Репозиторий статистики использования.

Обеспечивает учёт генераций и проверку лимитов.
"""

from datetime import UTC, date, datetime, time
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UsageLog, User, UserPlan


class UsageRepository:
    """Репозиторий для работы со статистикой использования."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_usage(
        self,
        user_id: UUID,
        labels_count: int,
        preflight_status: str | None = None,
    ) -> UsageLog:
        """
        Записать факт использования сервиса.

        Args:
            user_id: UUID пользователя
            labels_count: Количество сгенерированных этикеток
            preflight_status: Результат Pre-flight проверки (ok/warning/error)

        Returns:
            Созданная запись
        """
        usage = UsageLog(
            user_id=user_id,
            labels_count=labels_count,
            preflight_status=preflight_status,
        )
        self.session.add(usage)
        await self.session.flush()
        return usage

    async def get_daily_usage(
        self,
        user_id: UUID,
        target_date: date | None = None,
    ) -> int:
        """
        Получить количество этикеток за день.

        Args:
            user_id: UUID пользователя
            target_date: Дата (по умолчанию — сегодня)

        Returns:
            Количество этикеток
        """
        if target_date is None:
            target_date = date.today()

        # Начало и конец дня
        day_start = datetime.combine(target_date, time.min, tzinfo=UTC)
        day_end = datetime.combine(target_date, time.max, tzinfo=UTC)

        result = await self.session.execute(
            select(func.coalesce(func.sum(UsageLog.labels_count), 0))
            .where(UsageLog.user_id == user_id)
            .where(UsageLog.created_at >= day_start)
            .where(UsageLog.created_at <= day_end)
        )
        return result.scalar() or 0

    async def get_total_usage(self, user_id: UUID) -> int:
        """Получить общее количество сгенерированных этикеток."""
        result = await self.session.execute(
            select(func.coalesce(func.sum(UsageLog.labels_count), 0)).where(
                UsageLog.user_id == user_id
            )
        )
        return result.scalar() or 0

    async def get_usage_stats(self, user_id: UUID) -> dict:
        """
        Получить полную статистику использования.

        Returns:
            {
                "total_generated": int,
                "today_generated": int,
                "success_count": int,
                "warning_count": int,
                "error_count": int,
            }
        """
        today = date.today()
        day_start = datetime.combine(today, time.min, tzinfo=UTC)
        day_end = datetime.combine(today, time.max, tzinfo=UTC)

        # Общее количество
        total_result = await self.session.execute(
            select(func.coalesce(func.sum(UsageLog.labels_count), 0)).where(
                UsageLog.user_id == user_id
            )
        )
        total = total_result.scalar() or 0

        # За сегодня
        today_result = await self.session.execute(
            select(func.coalesce(func.sum(UsageLog.labels_count), 0))
            .where(UsageLog.user_id == user_id)
            .where(UsageLog.created_at >= day_start)
            .where(UsageLog.created_at <= day_end)
        )
        today_count = today_result.scalar() or 0

        # Подсчёт по статусам
        status_result = await self.session.execute(
            select(
                UsageLog.preflight_status,
                func.count(UsageLog.id),
            )
            .where(UsageLog.user_id == user_id)
            .group_by(UsageLog.preflight_status)
        )
        status_counts = {row[0] or "ok": row[1] for row in status_result.all()}

        return {
            "total_generated": total,
            "today_generated": today_count,
            "success_count": status_counts.get("ok", 0),
            "warning_count": status_counts.get("warning", 0),
            "error_count": status_counts.get("error", 0),
        }

    async def check_limit(
        self,
        user: User,
        labels_count: int,
        free_limit: int = 50,
    ) -> dict:
        """
        Проверить лимит пользователя.

        Новая логика (редизайн 2026-01-26):
        - FREE: 50 этикеток/месяц (накопления нет)
        - PRO: используется накопительный баланс (user.label_balance)
        - ENTERPRISE: безлимит

        Args:
            user: Пользователь
            labels_count: Количество этикеток для генерации
            free_limit: Лимит для Free (в месяц)

        Returns:
            {
                "allowed": bool,
                "remaining": int,
                "used_period": int,
                "limit": int,
                "plan": str,
            }
        """
        if user.plan == UserPlan.ENTERPRISE:
            return {
                "allowed": True,
                "remaining": 999999,
                "used_period": 0,
                "limit": 999999,
                "plan": user.plan.value,
            }

        if user.plan == UserPlan.PRO:
            # Для PRO лимит — это его текущий баланс
            remaining = user.label_balance
            allowed = remaining >= labels_count
            return {
                "allowed": allowed,
                "remaining": remaining,
                "used_period": 0,  # Для PRO не так важно сколько за день/месяц, важен баланс
                "limit": 10000,  # Максимальное накопление
                "plan": user.plan.value,
            }

        # FREE тариф — 50 в месяц
        used_this_month = await self.get_monthly_usage(user.id)
        limit = free_limit
        remaining = max(0, limit - used_this_month)
        allowed = remaining >= labels_count

        return {
            "allowed": allowed,
            "remaining": remaining,
            "used_period": used_this_month,
            "limit": limit,
            "monthly_limit": limit,
            "plan": user.plan.value,
        }

    async def get_history(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UsageLog]:
        """Получить историю использования."""
        result = await self.session.execute(
            select(UsageLog)
            .where(UsageLog.user_id == user_id)
            .order_by(UsageLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_monthly_usage(self, user_id: UUID) -> int:
        """Получить количество этикеток за текущий месяц."""
        today = date.today()
        month_start = datetime.combine(today.replace(day=1), time.min, tzinfo=UTC)

        result = await self.session.execute(
            select(func.coalesce(func.sum(UsageLog.labels_count), 0))
            .where(UsageLog.user_id == user_id)
            .where(UsageLog.created_at >= month_start)
        )
        return result.scalar() or 0
