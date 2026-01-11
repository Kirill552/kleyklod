"""
API эндпоинты для авторизации через Telegram Login Widget.

Проверка подписи Telegram и выдача JWT токенов.
"""

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.config import settings
from app.db.database import get_db, get_redis
from app.db.models import User
from app.models.schemas import (
    AuthTokenResponse,
    TelegramAuthData,
    UserResponse,
    VKAuthData,
    VKCodeAuthData,
)
from app.repositories import UserRepository
from app.services.auth import (
    create_access_token,
    verify_auth_date,
    verify_telegram_auth,
)
from app.services.rate_limiter import RateLimiter
from app.services.vk_auth import exchange_vk_code, get_vk_user_info

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

# Rate limit: 10 попыток в минуту на IP
AUTH_RATE_LIMIT = 10
AUTH_RATE_WINDOW = 60  # секунд


async def _get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency для получения UserRepository."""
    return UserRepository(db)


@router.post("/telegram", response_model=AuthTokenResponse)
async def telegram_login(
    auth_data: TelegramAuthData,
    request: Request,
    user_repo: UserRepository = Depends(_get_user_repo),
    redis: Redis = Depends(get_redis),
) -> AuthTokenResponse:
    """
    Авторизация через Telegram Login Widget.

    Процесс:
    1. Проверяем rate limit по IP
    2. Проверяем подпись данных от Telegram (HMAC-SHA256)
    3. Проверяем актуальность auth_date (не старше 24 часов)
    4. Находим или создаём пользователя в БД
    5. Генерируем JWT токен
    6. Возвращаем токен и данные пользователя

    Args:
        auth_data: Данные от Telegram Login Widget

    Returns:
        Токен доступа и информация о пользователе

    Raises:
        HTTPException 429: Слишком много попыток авторизации
        HTTPException 401: Если подпись невалидна или данные устарели
        HTTPException 500: При ошибке создания пользователя
    """
    # Rate limiting по IP
    client_ip = (
        request.headers.get("X-Real-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )

    rate_limiter = RateLimiter(redis)
    allowed, remaining, reset_ts = await rate_limiter.check_rate_limit(
        key=f"auth:{client_ip}",
        limit=AUTH_RATE_LIMIT,
        window_seconds=AUTH_RATE_WINDOW,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток авторизации. Попробуйте через минуту.",
            headers={"Retry-After": str(AUTH_RATE_WINDOW)},
        )

    # Конвертируем Pydantic модель в словарь для проверки подписи
    auth_dict = {
        "id": str(auth_data.id),
        "first_name": auth_data.first_name,
        "auth_date": str(auth_data.auth_date),
        "hash": auth_data.hash,
    }

    # Добавляем опциональные поля если они есть
    if auth_data.last_name:
        auth_dict["last_name"] = auth_data.last_name
    if auth_data.username:
        auth_dict["username"] = auth_data.username
    if auth_data.photo_url:
        auth_dict["photo_url"] = auth_data.photo_url

    # Проверяем подпись
    if not verify_telegram_auth(auth_dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительная подпись Telegram",
        )

    # Проверяем актуальность auth_date
    if not verify_auth_date(auth_data.auth_date):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Данные авторизации устарели",
        )

    # Находим или создаём пользователя
    user, is_new = await user_repo.get_or_create(
        telegram_id=auth_data.id,
        username=auth_data.username,
        first_name=auth_data.first_name,
    )

    # Если пользователь существует — обновляем его данные
    if not is_new:
        await user_repo.update_profile(
            user=user,
            username=auth_data.username,
            first_name=auth_data.first_name,
        )

    # Генерируем JWT токен
    access_token = create_access_token(user_id=str(user.id))

    # Формируем ответ
    user_response = UserResponse(
        id=user.id,
        telegram_id=auth_data.id,
        username=auth_data.username,
        first_name=auth_data.first_name,
        plan=user.plan,
        plan_expires_at=user.plan_expires_at,
        created_at=user.created_at,
    )

    return AuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,
    )


@router.post("/vk", response_model=AuthTokenResponse)
async def vk_login(
    auth_data: VKAuthData,
    request: Request,
    user_repo: UserRepository = Depends(_get_user_repo),
    redis: Redis = Depends(get_redis),
) -> AuthTokenResponse:
    """
    Авторизация через VK Mini App.

    Процесс:
    1. Проверяем rate limit по IP
    2. Находим или создаём пользователя в БД по VK ID
    3. Генерируем JWT токен
    4. Возвращаем токен и данные пользователя

    Args:
        auth_data: Данные от VK Mini App (vk_user_id, first_name, last_name)

    Returns:
        Токен доступа и информация о пользователе

    Raises:
        HTTPException 429: Слишком много попыток авторизации
    """
    # Rate limiting по IP
    client_ip = (
        request.headers.get("X-Real-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )

    rate_limiter = RateLimiter(redis)
    allowed, remaining, reset_ts = await rate_limiter.check_rate_limit(
        key=f"auth:vk:{client_ip}",
        limit=AUTH_RATE_LIMIT,
        window_seconds=AUTH_RATE_WINDOW,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток авторизации. Попробуйте через минуту.",
            headers={"Retry-After": str(AUTH_RATE_WINDOW)},
        )

    # Находим или создаём пользователя
    user, is_new = await user_repo.get_or_create_vk(
        vk_user_id=auth_data.vk_user_id,
        first_name=auth_data.first_name,
        last_name=auth_data.last_name,
    )

    # Если пользователь существует — обновляем его данные
    if not is_new:
        await user_repo.update_profile(
            user=user,
            first_name=auth_data.first_name,
            last_name=auth_data.last_name,
        )

    # Генерируем JWT токен
    access_token = create_access_token(user_id=str(user.id))

    # Формируем ответ
    user_response = UserResponse(
        id=user.id,
        vk_user_id=auth_data.vk_user_id,
        first_name=auth_data.first_name,
        plan=user.plan,
        plan_expires_at=user.plan_expires_at,
        created_at=user.created_at,
    )

    return AuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,
    )


@router.post("/vk/callback", response_model=AuthTokenResponse)
async def vk_code_login(
    auth_data: VKCodeAuthData,
    request: Request,
    user_repo: UserRepository = Depends(_get_user_repo),
    redis: Redis = Depends(get_redis),
) -> AuthTokenResponse:
    """
    Авторизация через VK One Tap на сайте (code flow).

    Процесс:
    1. Проверяем rate limit по IP
    2. Обмениваем code на access_token через VK ID API
    3. Получаем данные пользователя VK
    4. Находим или создаём пользователя в БД по vk_user_id
    5. Генерируем JWT токен
    6. Возвращаем токен и данные пользователя

    Args:
        auth_data: code + device_id от VK One Tap

    Returns:
        Токен доступа и информация о пользователе

    Raises:
        HTTPException 429: Слишком много попыток авторизации
        HTTPException 401: Ошибка обмена кода или получения данных VK
    """
    # Rate limiting по IP
    client_ip = (
        request.headers.get("X-Real-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )

    rate_limiter = RateLimiter(redis)
    allowed, remaining, reset_ts = await rate_limiter.check_rate_limit(
        key=f"auth:vk:callback:{client_ip}",
        limit=AUTH_RATE_LIMIT,
        window_seconds=AUTH_RATE_WINDOW,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток авторизации. Попробуйте через минуту.",
            headers={"Retry-After": str(AUTH_RATE_WINDOW)},
        )

    # 1. Обмениваем code на access_token через VK ID API
    vk_tokens = await exchange_vk_code(auth_data.code, auth_data.device_id, auth_data.code_verifier)

    # 2. Получаем данные пользователя VK
    vk_user_id = vk_tokens.get("user_id")
    vk_access_token = vk_tokens.get("access_token")
    vk_user = await get_vk_user_info(vk_access_token, vk_user_id)

    # 3. Находим или создаём пользователя (тот же метод что и для Mini App!)
    user, is_new = await user_repo.get_or_create_vk(
        vk_user_id=vk_user["id"],
        first_name=vk_user["first_name"],
        last_name=vk_user.get("last_name", ""),
    )

    # Если пользователь существует — обновляем его данные
    if not is_new:
        await user_repo.update_profile(
            user=user,
            first_name=vk_user["first_name"],
            last_name=vk_user.get("last_name"),
        )

    # 4. Генерируем JWT токен
    access_token = create_access_token(user_id=str(user.id))

    # 5. Формируем ответ
    user_response = UserResponse(
        id=user.id,
        vk_user_id=vk_user["id"],
        first_name=vk_user["first_name"],
        plan=user.plan,
        plan_expires_at=user.plan_expires_at,
        created_at=user.created_at,
    )

    return AuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,
    )


# ============== Transfer Token ==============
# Одноразовый токен для передачи авторизации между платформами

TRANSFER_TOKEN_TTL = 60  # секунд
TRANSFER_TOKEN_PREFIX = "transfer_token:"


class TransferTokenResponse(BaseModel):
    """Ответ с transfer token."""

    transfer_token: str
    expires_in: int


class TransferTokenRequest(BaseModel):
    """Запрос на обмен transfer token."""

    transfer_token: str


class VKTransferTokenRequest(BaseModel):
    """Запрос на создание transfer token для VK бота."""

    vk_user_id: int


@router.post("/transfer-token", response_model=TransferTokenResponse)
async def create_transfer_token(
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> TransferTokenResponse:
    """
    Создать одноразовый токен для передачи авторизации на сайт.

    Используется в VK Mini App для передачи авторизации при переходе на сайт.
    Токен действует 60 секунд и может быть использован только один раз.
    """
    # Генерируем случайный токен
    token = secrets.token_urlsafe(32)

    # Сохраняем в Redis: token -> user_id
    key = f"{TRANSFER_TOKEN_PREFIX}{token}"
    await redis.setex(key, TRANSFER_TOKEN_TTL, str(current_user.id))

    return TransferTokenResponse(
        transfer_token=token,
        expires_in=TRANSFER_TOKEN_TTL,
    )


@router.post("/transfer-token/exchange", response_model=AuthTokenResponse)
async def exchange_transfer_token(
    data: TransferTokenRequest,
    user_repo: UserRepository = Depends(_get_user_repo),
    redis: Redis = Depends(get_redis),
) -> AuthTokenResponse:
    """
    Обменять transfer token на JWT.

    Используется на сайте при переходе из VK Mini App или VK бота.
    Токен удаляется после использования (одноразовый).
    """
    key = f"{TRANSFER_TOKEN_PREFIX}{data.transfer_token}"

    # Получаем и удаляем токен (атомарно)
    user_id_str = await redis.getdel(key)

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или истекший токен",
        )

    # Получаем пользователя
    user = await user_repo.get_by_id(int(user_id_str))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    # Генерируем JWT токен
    access_token = create_access_token(user_id=str(user.id))

    # Формируем ответ
    user_response = UserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        vk_user_id=user.vk_user_id,
        username=user.username,
        first_name=user.first_name,
        plan=user.plan,
        plan_expires_at=user.plan_expires_at,
        created_at=user.created_at,
    )

    return AuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,
    )


@router.post("/transfer-token/vk", response_model=TransferTokenResponse, include_in_schema=False)
async def create_transfer_token_for_vk(
    data: VKTransferTokenRequest,
    x_bot_secret: str | None = Header(None, alias="X-Bot-Secret"),
    user_repo: UserRepository = Depends(_get_user_repo),
    redis: Redis = Depends(get_redis),
) -> TransferTokenResponse:
    """
    Создать transfer token для VK бота (внутренний endpoint).

    Используется VK ботом для генерации ссылки с авторизацией.
    Защищён X-Bot-Secret.
    """
    # Проверяем секрет бота
    if not x_bot_secret or x_bot_secret != settings.BOT_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный секрет бота",
        )

    # Находим пользователя по VK ID
    user = await user_repo.get_by_vk_id(data.vk_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден. Сначала авторизуйтесь через Mini App.",
        )

    # Генерируем случайный токен
    token = secrets.token_urlsafe(32)

    # Сохраняем в Redis
    key = f"{TRANSFER_TOKEN_PREFIX}{token}"
    await redis.setex(key, TRANSFER_TOKEN_TTL, str(user.id))

    return TransferTokenResponse(
        transfer_token=token,
        expires_in=TRANSFER_TOKEN_TTL,
    )
