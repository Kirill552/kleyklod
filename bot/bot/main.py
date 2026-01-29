"""
Точка входа для Telegram бота KleyKod.
"""

import asyncio

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import get_bot_settings
from bot.handlers import (
    apikey_router,
    chz_only_router,
    generate_router,
    history_router,
    payment_router,
    products_router,
    profile_router,
    start_router,
    support_router,
    wb_only_router,
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
    dp.include_router(wb_only_router)
    dp.include_router(chz_only_router)
    dp.include_router(profile_router)
    dp.include_router(apikey_router)
    dp.include_router(history_router)
    dp.include_router(support_router)
    dp.include_router(products_router)

    # Устанавливаем меню команд бота
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="settings", description="Настройки"),
        BotCommand(command="products", description="База товаров"),
        BotCommand(command="history", description="История генераций"),
        BotCommand(command="plans", description="Тарифы"),
        BotCommand(command="support", description="Поддержка"),
    ]
    await bot.set_my_commands(commands)
    logger.info("[COMMANDS] Меню команд установлено")

    # Запуск
    logger.info(f"[START] {settings.app_name} v{settings.app_version}")
    logger.info(f"API URL: {settings.api_base_url}")

    # Retry-логика для polling с exponential backoff
    max_retries = 10
    base_delay = 5  # секунд

    for attempt in range(max_retries):
        try:
            # Удаляем вебхук и запускаем polling
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
            break  # Нормальное завершение
        except TelegramNetworkError as e:
            delay = min(base_delay * (2**attempt), 300)  # макс 5 минут
            logger.warning(
                f"[NETWORK] Ошибка сети (попытка {attempt + 1}/{max_retries}): {e}. "
                f"Переподключение через {delay}с..."
            )
            await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"[ERROR] Критическая ошибка: {e}")
            raise
    else:
        logger.error("[FATAL] Превышено количество попыток переподключения")

    # Закрываем соединения
    await bot.session.close()
    if hasattr(storage, "_redis"):
        await storage._redis.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
