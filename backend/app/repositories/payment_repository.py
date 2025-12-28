"""
Репозиторий платежей.

Обеспечивает операции с платежами и подписками.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Payment, PaymentStatus, User, UserPlan


class PaymentRepository:
    """Репозиторий для работы с платежами."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        amount: int,
        currency: str,
        provider: str,
        plan: UserPlan | None = None,
        external_id: str | None = None,
    ) -> Payment:
        """
        Создать запись о платеже.

        Args:
            user_id: UUID пользователя
            amount: Сумма в копейках
            currency: Валюта (RUB)
            provider: Провайдер (yookassa)
            plan: Оплачиваемый тариф
            external_id: ID транзакции во внешней системе

        Returns:
            Созданный платёж
        """
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency=currency,
            provider=provider,
            plan=plan,
            external_id=external_id,
            status=PaymentStatus.PENDING,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        """Получить платёж по ID."""
        result = await self.session.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Payment | None:
        """Получить платёж по внешнему ID."""
        result = await self.session.execute(
            select(Payment).where(Payment.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def complete(self, payment: Payment) -> Payment:
        """Отметить платёж как завершённый."""
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.now(UTC)
        await self.session.flush()
        return payment

    async def fail(self, payment: Payment) -> Payment:
        """Отметить платёж как неудачный."""
        payment.status = PaymentStatus.FAILED
        await self.session.flush()
        return payment

    async def refund(self, payment: Payment) -> Payment:
        """Отметить платёж как возвращённый."""
        payment.status = PaymentStatus.REFUNDED
        await self.session.flush()
        return payment

    async def get_user_payments(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status: PaymentStatus | None = None,
    ) -> list[Payment]:
        """
        Получить платежи пользователя.

        Args:
            user_id: UUID пользователя
            limit: Максимум записей
            offset: Смещение
            status: Фильтр по статусу

        Returns:
            Список платежей
        """
        query = (
            select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc())
        )

        if status:
            query = query.where(Payment.status == status)

        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_completed_payments(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> list[Payment]:
        """Получить только успешные платежи."""
        return await self.get_user_payments(
            user_id=user_id,
            limit=limit,
            status=PaymentStatus.COMPLETED,
        )

    async def get_total_spent(
        self,
        user_id: UUID,
        currency: str = "RUB",
    ) -> int:
        """Получить общую сумму платежей."""
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.user_id == user_id)
            .where(Payment.currency == currency)
            .where(Payment.status == PaymentStatus.COMPLETED)
        )
        return result.scalar() or 0

    async def activate_subscription(
        self,
        user: User,
        payment: Payment,
        duration_days: int,
    ) -> User:
        """
        Активировать подписку после успешного платежа.

        Args:
            user: Пользователь
            payment: Платёж
            duration_days: Длительность подписки в днях

        Returns:
            Обновлённый пользователь
        """
        from datetime import timedelta

        # Определяем новый срок
        now = datetime.now(UTC)

        # Если есть активная подписка — продлеваем
        if user.plan_expires_at and user.plan_expires_at > now:
            expires_at = user.plan_expires_at + timedelta(days=duration_days)
        else:
            expires_at = now + timedelta(days=duration_days)

        # Обновляем пользователя
        user.plan = payment.plan or UserPlan.PRO
        user.plan_expires_at = expires_at

        # Отмечаем платёж как завершённый
        await self.complete(payment)

        await self.session.flush()
        return user
