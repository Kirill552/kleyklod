"""
Точка входа FastAPI приложения KleyKod.

Объединение этикеток Wildberries и Честного Знака.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, labels, users, payments
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle приложения.

    Инициализация при старте, очистка при завершении.
    """
    # Startup
    # TODO: Инициализация подключения к БД
    # TODO: Инициализация Redis
    print(f"[START] {settings.app_name} v{settings.app_version}")

    yield

    # Shutdown
    # TODO: Закрытие подключений
    print(f"[STOP] {settings.app_name}")


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
app.include_router(labels.router, prefix="/api/v1", tags=["Labels"])
app.include_router(users.router, tags=["Users"])
app.include_router(payments.router, tags=["Payments"])


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Корневой эндпоинт — редирект на документацию."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
