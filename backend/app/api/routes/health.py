"""
Health check эндпоинты.

Проверка состояния сервиса, БД и Redis.
"""

from fastapi import APIRouter

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
async def health_db() -> dict[str, str]:
    """
    Проверка подключения к базе данных.

    Returns:
        Статус подключения к PostgreSQL
    """
    # TODO: Реальная проверка подключения к БД
    return {"status": "ok", "database": "postgresql"}


@router.get("/health/redis")
async def health_redis() -> dict[str, str]:
    """
    Проверка подключения к Redis.

    Returns:
        Статус подключения к Redis
    """
    # TODO: Реальная проверка подключения к Redis
    return {"status": "ok", "cache": "redis"}
