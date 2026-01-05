"""
HTTP клиент для взаимодействия с Backend API.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from bot.config import get_bot_settings

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Ответ от API."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    status_code: int = 200


class APIClient:
    """
    Клиент для Backend API.

    Использует httpx для асинхронных запросов с retry логикой.
    """

    def __init__(self):
        settings = get_bot_settings()
        self.base_url = settings.api_base_url
        self.timeout = settings.api_timeout
        self.max_retries = 3
        self.retry_delay = 1.0  # секунды
        # Секрет для защищённых bot endpoints (IDOR protection)
        self._bot_secret = settings.bot_secret_key

    def _get_bot_headers(self) -> dict[str, str]:
        """Заголовки для защищённых bot endpoints."""
        if self._bot_secret:
            return {"X-Bot-Secret": self._bot_secret}
        return {}

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        retries: int = 3,
        **kwargs,
    ) -> httpx.Response:
        """
        Выполнить HTTP запрос с retry логикой.

        Args:
            method: HTTP метод (GET, POST, etc.)
            url: URL запроса
            retries: Количество попыток
            **kwargs: Аргументы для httpx

        Returns:
            Response объект

        Raises:
            httpx.RequestError: При неудаче всех попыток
        """
        last_exception = None

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, **kwargs)

                    # Успешный ответ или клиентская ошибка — не повторяем
                    if response.status_code < 500:
                        return response

                    # Серверная ошибка — повторяем
                    logger.warning(
                        f"[API] Попытка {attempt + 1}/{retries} неудачна: "
                        f"HTTP {response.status_code}"
                    )

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                logger.warning(
                    f"[API] Попытка {attempt + 1}/{retries} неудачна: {type(e).__name__}"
                )

            # Ждём перед следующей попыткой (экспоненциальный backoff)
            if attempt < retries - 1:
                delay = self.retry_delay * (2**attempt)
                await asyncio.sleep(delay)

        # Все попытки исчерпаны
        if last_exception:
            raise last_exception

        # Возвращаем последний ответ (с ошибкой сервера)
        return response

    async def preflight_check(
        self,
        wb_pdf: bytes,
        codes_file: bytes,
        codes_filename: str = "codes.csv",
    ) -> APIResponse:
        """Только Pre-flight проверка без генерации."""
        url = f"{self.base_url}/api/v1/labels/preflight"

        files = {
            "wb_pdf": ("wb_labels.pdf", wb_pdf, "application/pdf"),
            "codes_file": (codes_filename, codes_file, "text/csv"),
        }

        try:
            response = await self._request_with_retry(
                "POST",
                url,
                files=files,
                retries=self.max_retries,
            )

            if response.status_code == 200:
                return APIResponse(
                    success=True,
                    data=response.json(),
                    status_code=response.status_code,
                )
            else:
                return APIResponse(
                    success=False,
                    error="Ошибка Pre-flight проверки",
                    status_code=response.status_code,
                )

        except Exception as e:
            return APIResponse(
                success=False,
                error=str(e),
                status_code=500,
            )

    async def download_pdf(self, file_id: str) -> bytes | None:
        """Скачать сгенерированный PDF."""
        url = f"{self.base_url}/api/v1/labels/download/{file_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    return response.content
                return None

        except Exception:
            return None

    async def health_check(self) -> bool:
        """Проверка доступности API."""
        url = f"{self.base_url}/health"

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    async def get_user_profile(self, telegram_id: int) -> dict | None:
        """Получить профиль пользователя."""
        url = f"{self.base_url}/api/v1/users/{telegram_id}/profile"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_bot_headers())

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception:
            return None

    async def get_payment_history(self, telegram_id: int) -> list | None:
        """Получить историю платежей пользователя."""
        url = f"{self.base_url}/api/v1/users/{telegram_id}/payments"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_bot_headers())

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception:
            return None

    async def create_yookassa_payment(
        self,
        plan: str,
        telegram_id: int,
    ) -> dict | None:
        """
        Создать платёж через ЮКассу.

        Args:
            plan: Тарифный план (pro / enterprise)
            telegram_id: ID пользователя Telegram

        Returns:
            dict с payment_id и confirmation_url
        """
        url = f"{self.base_url}/api/v1/payments/create"

        payload = {
            "plan": plan,
            "telegram_id": telegram_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    return response.json()

                logger.error(f"[API] Ошибка создания платежа: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"[API] Исключение при создании платежа: {e}")
            return None

    async def activate_subscription(
        self,
        telegram_id: int,
        plan: str,
        duration_days: int,
        telegram_payment_charge_id: str,
        provider_payment_charge_id: str,
        total_amount: int,
    ) -> dict | None:
        """Активировать подписку после оплаты."""
        url = f"{self.base_url}/api/v1/payments/activate"

        payload = {
            "telegram_id": telegram_id,
            "plan": plan,
            "duration_days": duration_days,
            "telegram_payment_charge_id": telegram_payment_charge_id,
            "provider_payment_charge_id": provider_payment_charge_id,
            "total_amount": total_amount,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception:
            return None

    async def register_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> dict | None:
        """Зарегистрировать пользователя в системе."""
        url = f"{self.base_url}/api/v1/users/register"

        payload = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

                if response.status_code in (200, 201):
                    return response.json()
                return None

        except Exception:
            return None

    async def check_limit(self, telegram_id: int, labels_count: int = 1) -> dict | None:
        """
        Проверить лимит пользователя перед генерацией.

        Args:
            telegram_id: ID пользователя Telegram
            labels_count: Количество этикеток для генерации

        Returns:
            dict с полями: allowed, remaining, plan, used_today, daily_limit
        """
        url = f"{self.base_url}/api/v1/users/{telegram_id}/check-limit"
        params = {"labels_count": labels_count}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=self._get_bot_headers())

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception:
            return None

    # === API ключи ===

    async def create_api_key(self, telegram_id: int) -> APIResponse:
        """
        Создать новый API ключ для пользователя.

        Args:
            telegram_id: ID пользователя Telegram

        Returns:
            APIResponse с api_key и warning при успехе
        """
        url = f"{self.base_url}/api/v1/keys/bot/{telegram_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=self._get_bot_headers())

                if response.status_code == 200:
                    return APIResponse(
                        success=True,
                        data=response.json(),
                        status_code=response.status_code,
                    )
                else:
                    error_data = response.json() if response.content else {}
                    return APIResponse(
                        success=False,
                        error=error_data.get("detail", "Ошибка создания ключа"),
                        status_code=response.status_code,
                    )

        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Ошибка соединения: {str(e)}",
                status_code=503,
            )

    async def get_api_key_info(self, telegram_id: int) -> APIResponse:
        """
        Получить информацию о текущем API ключе.

        Args:
            telegram_id: ID пользователя Telegram

        Returns:
            APIResponse с prefix, created_at, last_used_at
        """
        url = f"{self.base_url}/api/v1/keys/bot/{telegram_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_bot_headers())

                if response.status_code == 200:
                    return APIResponse(
                        success=True,
                        data=response.json(),
                        status_code=response.status_code,
                    )
                else:
                    error_data = response.json() if response.content else {}
                    return APIResponse(
                        success=False,
                        error=error_data.get("detail", "Ошибка получения информации"),
                        status_code=response.status_code,
                    )

        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Ошибка соединения: {str(e)}",
                status_code=503,
            )

    async def revoke_api_key(self, telegram_id: int) -> APIResponse:
        """
        Отозвать API ключ пользователя.

        Args:
            telegram_id: ID пользователя Telegram

        Returns:
            APIResponse с message при успехе
        """
        url = f"{self.base_url}/api/v1/keys/bot/{telegram_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(url, headers=self._get_bot_headers())

                if response.status_code == 200:
                    return APIResponse(
                        success=True,
                        data=response.json(),
                        status_code=response.status_code,
                    )
                else:
                    error_data = response.json() if response.content else {}
                    return APIResponse(
                        success=False,
                        error=error_data.get("detail", "Ошибка отзыва ключа"),
                        status_code=response.status_code,
                    )

        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Ошибка соединения: {str(e)}",
                status_code=503,
            )

    # === История генераций ===

    async def get_generations(
        self,
        telegram_id: int,
        limit: int = 5,
        offset: int = 0,
    ) -> APIResponse:
        """
        Получить историю генераций пользователя.

        Args:
            telegram_id: ID пользователя Telegram
            limit: Количество записей на странице
            offset: Смещение от начала

        Returns:
            APIResponse с items и total
        """
        url = f"{self.base_url}/api/v1/generations/bot/{telegram_id}"
        params = {"limit": limit, "offset": offset}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_bot_headers(),
                )

                if response.status_code == 200:
                    return APIResponse(
                        success=True,
                        data=response.json(),
                        status_code=response.status_code,
                    )
                else:
                    error_data = response.json() if response.content else {}
                    return APIResponse(
                        success=False,
                        error=error_data.get("detail", "Ошибка получения истории"),
                        status_code=response.status_code,
                    )

        except Exception as e:
            logger.error(f"[API] Ошибка получения генераций: {e}")
            return APIResponse(
                success=False,
                error=f"Ошибка соединения: {str(e)}",
                status_code=503,
            )

    async def download_generation(
        self,
        telegram_id: int,
        generation_id: str,
    ) -> APIResponse:
        """
        Скачать файл генерации.

        Args:
            telegram_id: ID пользователя Telegram
            generation_id: UUID генерации

        Returns:
            APIResponse с содержимым файла в data
        """
        url = f"{self.base_url}/api/v1/generations/bot/{telegram_id}/{generation_id}/download"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self._get_bot_headers(),
                )

                if response.status_code == 200:
                    return APIResponse(
                        success=True,
                        data=response.content,
                        status_code=response.status_code,
                    )
                elif response.status_code == 410:
                    return APIResponse(
                        success=False,
                        error="Файл удалён (срок хранения истёк)",
                        status_code=response.status_code,
                    )
                else:
                    error_data = response.json() if response.content else {}
                    return APIResponse(
                        success=False,
                        error=error_data.get("detail", "Ошибка скачивания файла"),
                        status_code=response.status_code,
                    )

        except Exception as e:
            logger.error(f"[API] Ошибка скачивания генерации: {e}")
            return APIResponse(
                success=False,
                error=f"Ошибка соединения: {str(e)}",
                status_code=503,
            )

    # === Excel парсинг и генерация ===

    async def parse_excel_barcodes(
        self,
        excel_file: bytes,
        filename: str,
    ) -> dict | None:
        """
        Парсит Excel и возвращает информацию о колонках.

        Args:
            excel_file: Содержимое Excel файла
            filename: Имя файла

        Returns:
            dict с columns, detected_column, confidence, sample_items, total_count
            или None при ошибке
        """
        url = f"{self.base_url}/api/v1/labels/parse-excel"

        files = {
            "barcodes_excel": (
                filename,
                excel_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, files=files)

                if response.status_code == 200:
                    return response.json()

                logger.warning(f"[API] Ошибка парсинга Excel: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"[API] Исключение при парсинге Excel: {e}")
            return None

    async def generate_from_excel(
        self,
        excel_file: bytes,
        excel_filename: str,
        barcode_column: str,
        codes_file: bytes,
        codes_filename: str,
        telegram_id: int,
        label_format: str = "combined",
    ) -> APIResponse:
        """
        Генерация этикеток из Excel с баркодами.

        Args:
            excel_file: Excel файл с баркодами
            excel_filename: Имя Excel файла
            barcode_column: Выбранная колонка с баркодами (например "B" или "B: Баркод")
            codes_file: Файл с кодами ЧЗ
            codes_filename: Имя файла с кодами
            telegram_id: ID пользователя Telegram
            label_format: Формат этикеток (всегда "combined")

        Returns:
            APIResponse с результатом генерации
        """
        url = f"{self.base_url}/api/v1/labels/generate-full"

        # Извлекаем букву колонки если передан полный формат "B: Баркод"
        col_letter = barcode_column.split(":")[0].strip()

        files = {
            "barcodes_excel": (
                excel_filename,
                excel_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            "codes_file": (codes_filename, codes_file, "text/csv"),
        }
        data = {
            "barcode_column": col_letter,
            "template": "58x40",
            "label_format": label_format,
            "telegram_id": str(telegram_id),
        }

        try:
            response = await self._request_with_retry(
                "POST",
                url,
                files=files,
                data=data,
                retries=self.max_retries,
            )

            if response.status_code == 200:
                return APIResponse(
                    success=True,
                    data=response.json(),
                    status_code=response.status_code,
                )
            else:
                error_data = response.json() if response.content else {}
                return APIResponse(
                    success=False,
                    error=error_data.get("detail", "Ошибка генерации"),
                    status_code=response.status_code,
                )

        except httpx.TimeoutException:
            return APIResponse(
                success=False,
                error="Превышено время ожидания. Попробуйте позже.",
                status_code=504,
            )
        except httpx.RequestError as e:
            return APIResponse(
                success=False,
                error=f"Ошибка соединения: {str(e)}",
                status_code=503,
            )
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Неизвестная ошибка: {str(e)}",
                status_code=500,
            )

    # === Обратная связь ===

    async def submit_feedback(
        self,
        telegram_id: int,
        text: str,
        source: str = "bot",
    ) -> dict | None:
        """
        Отправить обратную связь.

        Args:
            telegram_id: ID пользователя Telegram
            text: Текст обратной связи
            source: Источник отзыва (bot / web)

        Returns:
            dict с результатом или None при ошибке
        """
        url = f"{self.base_url}/api/v1/feedback"

        payload = {
            "telegram_id": telegram_id,
            "text": text,
            "source": source,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

                if response.status_code in (200, 201):
                    return response.json()

                logger.warning(f"[API] Ошибка отправки feedback: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"[API] Исключение при отправке feedback: {e}")
            return None

    async def get_feedback_status(self, telegram_id: int) -> dict | None:
        """
        Проверить, нужно ли показывать опрос обратной связи.

        Args:
            telegram_id: ID пользователя Telegram

        Returns:
            dict с полями: should_ask, total_generated, feedback_asked
        """
        url = f"{self.base_url}/api/v1/feedback/status"
        params = {"telegram_id": telegram_id}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception as e:
            logger.warning(f"[API] Ошибка получения feedback status: {e}")
            return None


# Глобальный экземпляр
_api_client: APIClient | None = None


def get_api_client() -> APIClient:
    """Получить экземпляр API клиента."""
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client
