"""
Middleware для логирования запросов.
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех входящих сообщений."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        start_time = datetime.now()

        # Логируем входящее событие
        if isinstance(event, Message):
            user = event.from_user
            logger.info(
                f"Message from {user.id} (@{user.username}): {event.text or '[document/media]'}"
            )
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            logger.info(f"Callback from {user.id} (@{user.username}): {event.data}")

        # Выполняем обработчик
        result = await handler(event, data)

        # Логируем время выполнения
        duration = (datetime.now() - start_time).total_seconds()
        logger.debug(f"Handler completed in {duration:.3f}s")

        return result
