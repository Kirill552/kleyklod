"""
Сервис интеграции с ЮКасса.

Создание платежей, проверка статуса.
Используем официальный SDK yookassa.
"""

from typing import Any
from uuid import UUID

from yookassa import Configuration, Payment

from app.config import get_settings


class YooKassaService:
    """Сервис для работы с ЮКасса API через официальный SDK."""

    def __init__(self) -> None:
        settings = get_settings()
        # Конфигурируем SDK через метод configure()
        Configuration.configure(
            account_id=str(settings.yookassa_shop_id),
            secret_key=settings.yookassa_secret_key,
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

        # Создаём платёж через SDK
        payment = Payment.create(
            {
                "amount": {
                    "value": f"{amount}.00",
                    "currency": "RUB",
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": self.return_url,
                },
                "description": f"Подписка {plan.title()} на KleyKod",
                "metadata": metadata,
                "capture": True,
            }
        )

        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status,
        }

    async def get_payment(self, payment_id: str) -> dict[str, Any] | None:
        """Получить информацию о платеже."""
        try:
            payment = Payment.find_one(payment_id)

            return {
                "id": payment.id,
                "status": payment.status,
                "amount": float(payment.amount.value),
                "metadata": payment.metadata or {},
            }
        except Exception:
            return None
