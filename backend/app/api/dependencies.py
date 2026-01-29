"""
Dependencies для FastAPI эндпоинтов.

Зависимости для авторизации, получения текущего пользователя и т.д.
Поддерживает три метода аутентификации:
1. JWT токен (Authorization: Bearer <token>)
2. API ключ (X-API-Key: <key>) — только для Enterprise
3. Bot Secret (X-Bot-Secret: <key>) — для внутренних bot endpoints
"""

import hmac
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_db, get_redis
from app.db.models import User, UserPlan
from app.services.api_keys import ApiKeyService
from app.services.auth import decode_access_token
from app.services.rate_limiter import RateLimiter

settings = get_settings()


# === Bot Secret аутентификация (защита от IDOR) ===
# НЕ используем APIKeyHeader, чтобы не показывать в Swagger/OpenAPI


async def verify_bot_secret(request: Request) -> None:
    """
    Dependency для проверки секретного ключа бота.

    Используется для защиты bot endpoints от несанкционированного доступа.
    Бот передаёт секрет в заголовке X-Bot-Secret.

    NOTE: Не использует APIKeyHeader чтобы не отображаться в OpenAPI/Swagger.

    Raises:
        HTTPException 401: Если секрет отсутствует или неверен
        HTTPException 500: Если BOT_SECRET_KEY не настроен в production
    """
    if not settings.bot_secret_key:
        # В production BOT_SECRET_KEY обязателен
        if not settings.debug:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="BOT_SECRET_KEY not configured",
            )
        # В dev режиме пропускаем для обратной совместимости
        return

    secret = request.headers.get("X-Bot-Secret")

    # Используем hmac.compare_digest для защиты от timing attack
    if not secret or not hmac.compare_digest(secret, settings.bot_secret_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bot secret",
        )


# OAuth2 схема для получения токена из заголовка Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/telegram")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency для получения текущего авторизованного пользователя.

    Декодирует JWT токен, находит пользователя в БД.

    Args:
        token: JWT токен из заголовка Authorization
        db: Сессия БД

    Returns:
        Объект User

    Raises:
        HTTPException 401: Если токен невалиден или пользователь не найден
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Декодируем токен
    user_id_str = decode_access_token(token)
    if user_id_str is None:
        raise credentials_exception

    # Конвертируем в UUID
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # Ищем пользователя в БД
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # Проверяем что пользователь активен
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency для получения активного пользователя.

    Алиас для get_current_user (проверка активности уже внутри).

    Args:
        current_user: Текущий пользователь

    Returns:
        Объект User
    """
    return current_user


# === API Key аутентификация ===

# Схема для получения API ключа из заголовка X-API-Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_user_from_api_key(
    api_key: Annotated[str | None, Depends(api_key_header)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency для аутентификации по API ключу.

    Используется для эндпоинтов, доступных через API.
    Только для Enterprise пользователей.

    Args:
        api_key: API ключ из заголовка X-API-Key
        db: Сессия БД

    Returns:
        Объект User

    Raises:
        HTTPException 401: Если ключ отсутствует или невалиден
        HTTPException 403: Если подписка истекла или не Enterprise
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "API_KEY_MISSING", "message": "Заголовок X-API-Key отсутствует"},
        )

    # Ищем пользователя по ключу
    key_service = ApiKeyService(db)
    result = await key_service.find_user_by_api_key(api_key)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "API_KEY_INVALID", "message": "Неверный API ключ"},
        )

    user, key_record = result

    # Проверяем подписку Enterprise
    if user.plan != UserPlan.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_ENTERPRISE", "message": "API доступен только для Enterprise"},
        )

    # Проверяем срок подписки
    if user.plan_expires_at and user.plan_expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SUBSCRIPTION_EXPIRED", "message": "Подписка Enterprise истекла"},
        )

    # Проверяем что пользователь активен
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_INACTIVE", "message": "Пользователь деактивирован"},
        )

    # Обновляем last_used_at
    await key_service.update_last_used(key_record)

    return user


async def check_api_rate_limit(
    user: Annotated[User, Depends(get_user_from_api_key)],
    redis: Redis = Depends(get_redis),
) -> tuple[User, int, int]:
    """
    Dependency для проверки rate limit API запросов.

    Лимит: 100 запросов в минуту на одного пользователя.

    Args:
        user: Пользователь (из API ключа)
        redis: Redis клиент

    Returns:
        (user, remaining, reset_timestamp)

    Raises:
        HTTPException 429: Если превышен лимит
    """
    limiter = RateLimiter(redis)
    allowed, remaining, reset_ts = await limiter.check_rate_limit(
        key=str(user.id),
        limit=100,
        window_seconds=60,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RATE_LIMITED", "message": "Превышен лимит запросов"},
            headers={
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_ts),
                "Retry-After": "60",
            },
        )

    return user, remaining, reset_ts


# === Admin API Key аутентификация ===


async def get_admin_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> str:
    """
    Проверка X-API-Key для админских операций.

    Используется для управления статьями через API.

    Args:
        x_api_key: API ключ из заголовка X-API-Key

    Returns:
        Валидный API ключ

    Raises:
        HTTPException 401: Если ключ невалиден или не совпадает с ADMIN_API_KEY
    """
    if x_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key
