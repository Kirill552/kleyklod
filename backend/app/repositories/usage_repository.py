"""
Репозиторий статистики использования.

Обеспечивает учёт генераций и проверку лимитов.
"""

from datetime import date, datetime, time, timezone
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
        day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

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
            select(func.coalesce(func.sum(UsageLog.labels_count), 0))
            .where(UsageLog.user_id == user_id)
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
        day_start = datetime.combine(today, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(today, time.max, tzinfo=timezone.utc)

        # Общее количество
        total_result = await self.session.execute(
            select(func.coalesce(func.sum(UsageLog.labels_count), 0))
            .where(UsageLog.user_id == user_id)
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
        pro_limit: int = 500,
    ) -> dict:
        """
        Проверить лимит пользователя.

        Args:
            user: Пользователь
            labels_count: Количество этикеток для генерации
            free_limit: Лимит для Free
            pro_limit: Лимит для Pro

        Returns:
            {
                "allowed": bool,
                "remaining": int,
                "used_today": int,
                "daily_limit": int,
                "plan": str,
            }
        """
        # Определяем лимит по тарифу
        if user.plan == UserPlan.FREE:
            daily_limit = free_limit
        elif user.plan == UserPlan.PRO:
            daily_limit = pro_limit
        else:  # ENTERPRISE
            daily_limit = 999999  # Безлимит

        # Получаем использование за сегодня
        used_today = await self.get_daily_usage(user.id)
        remaining = max(0, daily_limit - used_today)
        allowed = remaining >= labels_count

        return {
            "allowed": allowed,
            "remaining": remaining,
            "used_today": used_today,
            "daily_limit": daily_limit,
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
