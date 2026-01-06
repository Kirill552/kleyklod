"""
Health check эндпоинты.

Проверка состояния сервиса, БД и Redis.
"""

import sentry_sdk
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db, get_redis

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Базовая проверка состояния сервиса.

    Returns:
        Статус "ok" если сервис работает
    """
    return {"status": "ok"}


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """
    Проверка подключения к базе данных.

    Returns:
        Статус подключения к PostgreSQL
    """
    try:
        # Выполняем простой запрос для проверки соединения
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "postgresql"}
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return {"status": "error", "database": "postgresql", "error": str(e)}


@router.get("/health/redis")
async def health_redis(redis: Redis = Depends(get_redis)) -> dict[str, str]:
    """
    Проверка подключения к Redis.

    Returns:
        Статус подключения к Redis
    """
    try:
        # Пингуем Redis
        await redis.ping()
        return {"status": "ok", "cache": "redis"}
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return {"status": "error", "cache": "redis", "error": str(e)}


@router.get("/health/full")
async def health_full(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """
    Полная проверка всех компонентов.

    Returns:
        Статус всех сервисов
    """
    db_ok = False
    redis_ok = False
    errors = []

    # Проверяем DB
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        sentry_sdk.capture_exception(e)
        errors.append(f"db: {e}")

    # Проверяем Redis
    try:
        await redis.ping()
        redis_ok = True
    except Exception as e:
        sentry_sdk.capture_exception(e)
        errors.append(f"redis: {e}")

    overall_status = "ok" if (db_ok and redis_ok) else "degraded"

    return {
        "status": overall_status,
        "components": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
        "errors": errors if errors else None,
    }
