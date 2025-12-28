"""
Сервис интеграции с ЮКасса.

Создание платежей, проверка статуса.
"""

from uuid import UUID

from aioyookassa import YooKassa
from aioyookassa.types.enum import ConfirmationType, Currency
from aioyookassa.types.params import CreatePaymentParams
from aioyookassa.types.payment import Confirmation, Money

from app.config import get_settings


class YooKassaService:
    """Сервис для работы с ЮКасса API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = YooKassa(
            api_key=settings.yookassa_secret_key,
            shop_id=settings.yookassa_shop_id,
        )
        self.return_url = settings.yookassa_return_url

    async def create_payment(
        self,
        amount: int,  # В рублях
        plan: str,
        user_id: UUID | None = None,
        telegram_id: int | None = None,
        source: str = "web",
    ) -> dict[str, str]:
        """
        Создать платёж в ЮКассе.

        Args:
            amount: Сумма в рублях
            plan: Тариф (pro/enterprise)
            user_id: UUID пользователя
            telegram_id: Telegram ID (для бота)
            source: Источник (web/bot)

        Returns:
            dict с payment_id и confirmation_url
        """
        metadata: dict[str, str] = {
            "plan": plan,
            "source": source,
        }
        if user_id:
            metadata["user_id"] = str(user_id)
        if telegram_id:
            metadata["telegram_id"] = str(telegram_id)

        params = CreatePaymentParams(
            amount=Money(value=float(amount), currency=Currency.RUB),
            confirmation=Confirmation(
                type=ConfirmationType.REDIRECT,
                return_url=self.return_url,
            ),
            description=f"Подписка {plan.title()} на KleyKod",
            metadata=metadata,
            capture=True,
        )

        payment = await self.client.payments.create_payment(params)

        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status,
        }

    async def get_payment(self, payment_id: str) -> dict[str, str | float | dict[str, str]] | None:
        """Получить информацию о платеже."""
        try:
            payment = await self.client.payments.get_payment_info(payment_id)
            return {
                "id": payment.id,
                "status": payment.status,
                "amount": payment.amount.value,
                "metadata": payment.metadata,
            }
        except Exception:
            return None
