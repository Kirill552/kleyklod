"""
Middleware для rate limiting.
"""

import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """
    Простой rate limiter на основе памяти.

    Для продакшена рекомендуется использовать Redis.
    """

    def __init__(
        self,
        max_requests: int = 30,
        window_seconds: int = 60,
    ):
        """
        Args:
            max_requests: Максимум запросов за период
            window_seconds: Период в секундах
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[int, list[datetime]] = defaultdict(list)

    def _cleanup_old_requests(self, user_id: int) -> None:
        """Удаление устаревших запросов."""
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id] if req_time > cutoff
        ]

    def _is_rate_limited(self, user_id: int) -> bool:
        """Проверка превышения лимита."""
        self._cleanup_old_requests(user_id)
        return len(self.requests[user_id]) >= self.max_requests

    def _record_request(self, user_id: int) -> None:
        """Запись нового запроса."""
        self.requests[user_id].append(datetime.now())

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Получаем user_id
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id is None:
            return await handler(event, data)

        # Проверяем rate limit
        if self._is_rate_limited(user_id):
            logger.warning(f"Rate limit exceeded for user {user_id}")

            # Отправляем предупреждение
            if isinstance(event, Message):
                await event.answer("Слишком много запросов. Подождите немного.")
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "Слишком много запросов. Подождите.",
                    show_alert=True,
                )
            return None

        # Записываем запрос и выполняем обработчик
        self._record_request(user_id)
        return await handler(event, data)
