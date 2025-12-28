"""
Сервис интеграции с ЮКасса.

Создание платежей, проверка статуса.
Используем httpx с Basic Auth (официальный метод аутентификации ЮKassa).
"""

import uuid
from typing import Any
from uuid import UUID

import httpx

from app.config import get_settings


class YooKassaService:
    """Сервис для работы с ЮКасса API через httpx."""

    BASE_URL = "https://api.yookassa.ru/v3"

    def __init__(self) -> None:
        settings = get_settings()
        self.shop_id = settings.yookassa_shop_id
        self.secret_key = settings.yookassa_secret_key
        self.return_url = settings.yookassa_return_url

    def _get_auth(self) -> httpx.BasicAuth:
        """Basic Auth с ShopID и SecretKey."""
        # shop_id должен быть строкой для BasicAuth
        return httpx.BasicAuth(str(self.shop_id), self.secret_key)

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

        payload = {
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

        # Ключ идемпотентности для защиты от дублирования
        idempotence_key = str(uuid.uuid4())

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/payments",
                json=payload,
                auth=self._get_auth(),
                headers={
                    "Idempotence-Key": idempotence_key,
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("description", "Неизвестная ошибка")
                raise Exception(f"Ошибка создания платежа в ЮКассе: {error_msg}")

            payment = response.json()

        return {
            "payment_id": payment["id"],
            "confirmation_url": payment["confirmation"]["confirmation_url"],
            "status": payment["status"],
        }

    async def get_payment(self, payment_id: str) -> dict[str, Any] | None:
        """Получить информацию о платеже."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/payments/{payment_id}",
                    auth=self._get_auth(),
                )

                if response.status_code != 200:
                    return None

                payment = response.json()

            return {
                "id": payment["id"],
                "status": payment["status"],
                "amount": float(payment["amount"]["value"]),
                "metadata": payment.get("metadata", {}),
            }
        except Exception:
            return None
