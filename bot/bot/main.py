"""
Точка входа для Telegram бота KleyKod.
"""

import asyncio

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import get_bot_settings
from bot.handlers import (
    apikey_router,
    generate_router,
    history_router,
    payment_router,
    profile_router,
    start_router,
)
from bot.logging_config import get_logger, setup_logging
from bot.middlewares import AuthMiddleware, LoggingMiddleware, RateLimitMiddleware

# Настройка централизованного логирования (JSON в production)
setup_logging()
logger = get_logger(__name__)

# Инициализация Sentry/GlitchTip для мониторинга ошибок
_settings = get_bot_settings()
if _settings.sentry_dsn:
    sentry_sdk.init(
        dsn=_settings.sentry_dsn,
        environment="production" if not _settings.debug else "development",
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
    logger.info("[SENTRY] Мониторинг ошибок инициализирован")


async def get_storage(redis_url: str):
    """
    Получить хранилище для FSM.

    Пытается подключиться к Redis, при неудаче использует MemoryStorage.
    """
    try:
        from aiogram.fsm.storage.redis import RedisStorage
        from redis.asyncio import Redis

        redis = Redis.from_url(redis_url)
        # Проверяем подключение
        await redis.ping()
        logger.info("[REDIS] Подключено к Redis для FSM storage")
        return RedisStorage(redis)

    except ImportError:
        logger.warning("[REDIS] aiogram.fsm.storage.redis недоступен, используется MemoryStorage")
        return MemoryStorage()

    except Exception as e:
        logger.warning(f"[REDIS] Не удалось подключиться к Redis: {e}. Используется MemoryStorage")
        return MemoryStorage()


async def main():
    """Запуск бота."""
    settings = get_bot_settings()

    # Создаём бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Создаём хранилище для FSM
    storage = await get_storage(settings.redis_url)

    # Создаём диспетчер
    dp = Dispatcher(storage=storage)

    # Регистрируем middleware
    # Порядок важен: сначала логирование, потом rate limit, потом авторизация
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.message.middleware(RateLimitMiddleware(max_requests=30, window_seconds=60))
    dp.callback_query.middleware(RateLimitMiddleware(max_requests=50, window_seconds=60))
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Регистрируем роутеры
    # ВАЖНО: payment_router должен быть ПЕРЕД start_router
    # чтобы deep link обработчик (/start с аргументами) срабатывал первым
    dp.include_router(payment_router)
    dp.include_router(start_router)
    dp.include_router(generate_router)
    dp.include_router(profile_router)
    dp.include_router(apikey_router)
    dp.include_router(history_router)

    # Устанавливаем меню команд бота
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="settings", description="Настройки"),
        BotCommand(command="history", description="История генераций"),
        BotCommand(command="plans", description="Тарифы"),
    ]
    await bot.set_my_commands(commands)
    logger.info("[COMMANDS] Меню команд установлено")

    # Запуск
    logger.info(f"[START] {settings.app_name} v{settings.app_version}")
    logger.info(f"API URL: {settings.api_base_url}")

    try:
        # Удаляем вебхук и запускаем polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        # Закрываем Redis если используется
        if hasattr(storage, "_redis"):
            await storage._redis.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
