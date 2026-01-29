import os
import sys

# Добавляем путь к родительской директории для импорта app модулей
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db.models import LabelTransaction, TransactionType, User, UserPlan

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


async def migrate_pro_users():
    """
    Миграция существующих PRO пользователей на новую накопительную систему.
    Начисляет стартовые 2000 этикеток.
    """
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Находим всех PRO пользователей
        stmt = select(User).where(User.plan == UserPlan.PRO)
        result = await session.execute(stmt)
        pro_users = result.scalars().all()

        logger.info(f"Найдено {len(pro_users)} пользователей с тарифом Про")

        count = 0
        for user in pro_users:
            # Начисляем 2000 этикеток если баланс 0
            if user.label_balance == 0:
                user.label_balance = 2000

                # Создаем транзакцию миграции
                transaction = LabelTransaction(
                    user_id=user.id,
                    type=TransactionType.CREDIT,
                    amount=2000,
                    balance_after=2000,
                    reason="migration",
                    description="Стартовое начисление при переходе на накопительную систему",
                )
                session.add(transaction)
                count += 1
                logger.info(f"Начислено 2000 этикеток пользователю {user.id}")

        if count > 0:
            await session.commit()
            logger.info(f"Успешно мигрировано {count} пользователей")
        else:
            logger.info("Нет пользователей для миграции")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate_pro_users())
