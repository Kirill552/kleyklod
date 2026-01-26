import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LabelTransaction, TransactionType, User, UserPlan

logger = logging.getLogger(__name__)


class LabelBalanceService:
    """
    Сервис для управления балансом этикеток пользователей.
    Реализует накопительную систему для тарифа PRO.
    """

    ACCUMULATION_CAP = 10000  # Максимальный баланс для тарифа PRO

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_user_for_update(self, user_id: uuid.UUID) -> User:
        """Получить пользователя с блокировкой строки для обновления."""
        stmt = select(User).where(User.id == user_id).with_for_update()
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user

    async def credit_labels(
        self,
        user_id: uuid.UUID,
        amount: int,
        reason: str,
        reference_id: uuid.UUID = None,
        description: str = None,
    ) -> int:
        """
        Начислить этикетки на баланс пользователя.
        Для тарифа PRO применяется лимит накопления (10 000 шт).
        """
        user = await self._get_user_for_update(user_id)

        old_balance = user.label_balance
        new_balance = old_balance + amount

        # Применяем лимит накопления только для PRO
        if user.plan == UserPlan.PRO:
            if new_balance > self.ACCUMULATION_CAP:
                new_balance = self.ACCUMULATION_CAP

        user.label_balance = new_balance

        # Создаем транзакцию
        transaction = LabelTransaction(
            user_id=user_id,
            type=TransactionType.CREDIT,
            amount=amount,
            balance_after=new_balance,
            reason=reason,
            reference_id=reference_id,
            description=description,
        )
        self.db.add(transaction)
        await self.db.commit()

        logger.info(
            f"Credited {amount} labels to user {user_id}. New balance: {new_balance} (reason: {reason})"
        )
        return new_balance

    async def debit_labels(
        self,
        user_id: uuid.UUID,
        amount: int,
        reason: str = "generation",
        reference_id: uuid.UUID = None,
        description: str = None,
    ) -> int:
        """
        Списать этикетки с баланса пользователя.
        """
        user = await self._get_user_for_update(user_id)

        if user.label_balance < amount:
            raise ValueError(f"Insufficient balance: requested {amount}, have {user.label_balance}")

        new_balance = user.label_balance - amount
        user.label_balance = new_balance

        # Создаем транзакцию
        transaction = LabelTransaction(
            user_id=user_id,
            type=TransactionType.DEBIT,
            amount=amount,
            balance_after=new_balance,
            reason=reason,
            reference_id=reference_id,
            description=description,
        )
        self.db.add(transaction)
        await self.db.commit()

        logger.info(
            f"Debited {amount} labels from user {user_id}. New balance: {new_balance} (reason: {reason})"
        )
        return new_balance

    async def get_transactions(self, user_id: uuid.UUID, limit: int = 50) -> list[LabelTransaction]:
        """Получить историю транзакций пользователя."""
        stmt = (
            select(LabelTransaction)
            .where(LabelTransaction.user_id == user_id)
            .order_by(LabelTransaction.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
