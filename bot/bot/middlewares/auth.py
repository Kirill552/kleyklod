"""
Middleware для автоматической регистрации пользователей.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.utils import get_api_client

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки и регистрации пользователей.

    Автоматически регистрирует новых пользователей в системе.
    """

    def __init__(self):
        # Кэш зарегистрированных пользователей (в памяти)
        # Для продакшена использовать Redis
        self._registered_users: set[int] = set()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Получаем пользователя
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user is None:
            return await handler(event, data)

        # Проверяем кэш
        if user.id not in self._registered_users:
            # Регистрируем пользователя
            api = get_api_client()
            result = await api.register_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )

            if result:
                self._registered_users.add(user.id)
                logger.info(f"User {user.id} registered or confirmed")
            else:
                # API недоступен — продолжаем работу
                logger.warning(f"Could not register user {user.id}")

        return await handler(event, data)
