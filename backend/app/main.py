"""
Точка входа FastAPI приложения KleyKod.

Объединение этикеток Wildberries и Честного Знака.
"""

import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, generations, health, keys, labels, payments, users
from app.config import get_settings
from app.db.database import close_redis, init_redis
from app.tasks import start_cleanup_loop

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle приложения.

    Инициализация при старте, очистка при завершении.
    """
    # Startup
    logger.info(f"[START] {settings.app_name} v{settings.app_version}")

    # Инициализируем Redis (для rate limiting и кэша)
    await init_redis()
    logger.info("[REDIS] Подключение установлено")

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
* **Pre-flight проверка** — валидация размера DataMatrix и контрастности до печати
* **Freemium модель** — 50 этикеток в день бесплатно

### Killer Features:

* ⚡ Скорость: 1000 этикеток за 5 секунд
* 🔍 Pre-flight Check: проверка качества до печати
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
app.include_router(labels.router, prefix="/api/v1", tags=["Labels"])
app.include_router(users.router, tags=["Users"])
app.include_router(generations.router, tags=["Generations"])
app.include_router(payments.router, tags=["Payments"])
app.include_router(keys.router, tags=["API Keys"])


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Корневой эндпоинт — редирект на документацию."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
