"""
API эндпоинты для авторизации через Telegram Login Widget.

Проверка подписи Telegram и выдача JWT токенов.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.schemas import AuthTokenResponse, TelegramAuthData, UserResponse
from app.repositories import UserRepository
from app.services.auth import create_access_token, verify_auth_date, verify_telegram_auth

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


async def _get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency для получения UserRepository."""
    return UserRepository(db)


@router.post("/telegram", response_model=AuthTokenResponse)
async def telegram_login(
    auth_data: TelegramAuthData,
    user_repo: UserRepository = Depends(_get_user_repo),
) -> AuthTokenResponse:
    """
    Авторизация через Telegram Login Widget.

    Процесс:
    1. Проверяем подпись данных от Telegram (HMAC-SHA256)
    2. Проверяем актуальность auth_date (не старше 24 часов)
    3. Находим или создаём пользователя в БД
    4. Генерируем JWT токен
    5. Возвращаем токен и данные пользователя

    Args:
        auth_data: Данные от Telegram Login Widget

    Returns:
        Токен доступа и информация о пользователе

    Raises:
        HTTPException 401: Если подпись невалидна или данные устарели
        HTTPException 500: При ошибке создания пользователя
    """
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
