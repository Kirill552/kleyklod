"""
Точка входа FastAPI приложения KleyKod.

Объединение этикеток Wildberries и Честного Знака.
"""

import asyncio
import contextlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    config,
    demo,
    feedback,
    generations,
    health,
    keys,
    labels,
    payments,
    products,
    users,
)
from app.config import get_settings
from app.db.database import close_redis, init_redis
from app.logging_config import get_logger, setup_logging
from app.tasks import start_cleanup_loop

# TODO: Временно отключено из-за проблемы с дублирующимися хешами
# from app.tasks.populate_telegram_id_hash import populate_telegram_id_hashes

# Настройка централизованного логирования (JSON в production)
setup_logging()

settings = get_settings()
logger = get_logger(__name__)

# Инициализация Sentry/GlitchTip для мониторинга ошибок
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment="production" if not settings.debug else "development",
        traces_sample_rate=0.1,  # 10% транзакций для трейсинга
        profiles_sample_rate=0.1,  # 10% профилирования
        send_default_pii=False,  # Не отправлять персональные данные
    )
    logger.info("[SENTRY] Мониторинг ошибок инициализирован")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle приложения.

    Инициализация при старте, очистка при завершении.
    """
    # Startup
    logger.info(f"[START] {settings.app_name} v{settings.app_version}")

    # Создаём директорию для хранения генераций
    generations_dir = Path("data/generations")
    generations_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"[STORAGE] Директория для генераций: {generations_dir.absolute()}")

    # Инициализируем Redis (для rate limiting и кэша)
    await init_redis()
    logger.info("[REDIS] Подключение установлено")

    # TODO: Миграция telegram_id_hash временно отключена из-за проблемы с расшифровкой
    # Все пользователи получают одинаковый хеш - нужно проверить ENCRYPTION_KEY
    # async with get_db_session() as db:
    #     updated = await populate_telegram_id_hashes(db)
    #     if updated > 0:
    #         logger.info(f"[MIGRATION] Заполнено telegram_id_hash для {updated} пользователей")

    # Запускаем фоновую задачу очистки истекших генераций
    cleanup_task = asyncio.create_task(start_cleanup_loop(interval_hours=24))

    yield

    # Shutdown
    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task

    # Закрываем Redis
    await close_redis()
    logger.info("[REDIS] Соединение закрыто")

    logger.info(f"[STOP] {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## KleyKod API

Сервис для объединения этикеток Wildberries и кодов маркировки "Честный Знак" в одну наклейку.

### Возможности:

* **Объединение этикеток** — PDF WB + CSV/Excel коды ЧЗ → готовый PDF 58x40мм
* **Проверка качества** — валидация размера DataMatrix и контрастности до печати
* **Freemium модель** — 50 этикеток в день бесплатно

### Killer Features:

* ⚡ Скорость: 1000 этикеток за 5 секунд
* 🔍 Проверка качества: валидация до печати
* 💰 Прозрачные цены: без скрытых лимитов
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключение роутеров
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(demo.router, tags=["Demo"])
app.include_router(labels.router, prefix="/api/v1", tags=["Labels"])
app.include_router(users.router, tags=["Users"])
app.include_router(generations.router, tags=["Generations"])
app.include_router(payments.router, tags=["Payments"])
app.include_router(keys.router, tags=["API Keys"])
app.include_router(feedback.router, tags=["Feedback"])
app.include_router(config.router, tags=["Config"])
app.include_router(products.router, tags=["Products"])


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Корневой эндпоинт — редирект на документацию."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
