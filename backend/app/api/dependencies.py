"""
Dependencies для FastAPI эндпоинтов.

Зависимости для авторизации, получения текущего пользователя и т.д.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.services.auth import decode_access_token

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
