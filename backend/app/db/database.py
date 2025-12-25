"""
Подключение к базе данных PostgreSQL и Redis.

Асинхронное подключение через asyncpg и redis.asyncio.
"""

from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Создаём асинхронный движок
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Логирование SQL в debug режиме
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Проверка соединения перед использованием
)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД.

    Использование в FastAPI:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Инициализация БД (создание таблиц).

    Вызывать при старте приложения (в lifespan).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Закрытие соединений с БД."""
    await engine.dispose()


# === Redis ===

# Глобальный Redis клиент (инициализируется при старте)
_redis_client: Redis | None = None


async def init_redis() -> Redis:
    """
    Инициализация Redis клиента.

    Вызывать при старте приложения (в lifespan).
    """
    global _redis_client
    _redis_client = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    return _redis_client


async def close_redis() -> None:
    """Закрытие соединения с Redis."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Dependency для получения Redis клиента.

    Использование в FastAPI:
        async def endpoint(redis: Redis = Depends(get_redis)):
            ...
    """
    if _redis_client is None:
        raise RuntimeError("Redis не инициализирован. Вызовите init_redis() при старте.")
    yield _redis_client
