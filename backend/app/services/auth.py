"""
Сервис авторизации через Telegram Login Widget.

Проверка подписи и генерация JWT токенов.
"""

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def verify_telegram_auth(data: dict[str, str | int]) -> bool:
    """
    Проверяет подпись Telegram Login Widget.

    Алгоритм проверки:
    1. Создаём data_check_string из всех полей кроме hash (отсортированных по алфавиту)
    2. Вычисляем HMAC-SHA256 с секретным ключом (SHA-256 от BOT_TOKEN)
    3. Сравниваем с переданным hash

    Args:
        data: Данные от Telegram (id, first_name, auth_date, hash и т.д.)

    Returns:
        True если подпись валидна, False иначе
    """
    # Проверяем что telegram_bot_token установлен
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен в настройках")

    # Извлекаем hash из данных
    received_hash = data.get("hash")
    if not received_hash:
        return False

    # Создаём data_check_string из всех полей кроме hash
    # Формат: key=value\n для каждого поля, отсортированных по ключу
    check_data = {k: v for k, v in data.items() if k != "hash"}
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(check_data.items()))

    # Создаём секретный ключ: SHA-256 от BOT_TOKEN
    secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()

    # Вычисляем HMAC-SHA256
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    # Сравниваем хеши
    return hmac.compare_digest(expected_hash, str(received_hash))


def verify_auth_date(auth_date: int, max_age_hours: int = 24) -> bool:
    """
    Проверяет актуальность auth_date (не старше max_age_hours).

    Args:
        auth_date: Unix timestamp авторизации
        max_age_hours: Максимальный возраст в часах (по умолчанию 24)

    Returns:
        True если auth_date актуален, False иначе
    """
    current_time = datetime.now(UTC)
    auth_datetime = datetime.fromtimestamp(auth_date, tz=UTC)
    time_diff = current_time - auth_datetime

    return time_diff <= timedelta(hours=max_age_hours)


def create_access_token(user_id: str) -> str:
    """
    Создаёт JWT токен доступа.

    Args:
        user_id: UUID пользователя (строка)

    Returns:
        JWT токен
    """
    # Вычисляем время истечения токена
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_expire_days)

    # Формируем payload
    payload = {
        "sub": user_id,  # subject — ID пользователя
        "exp": expire,  # expiration time
        "iat": datetime.now(UTC),  # issued at
    }

    # Генерируем токен
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str) -> str | None:
    """
    Декодирует JWT токен и возвращает user_id.

    Args:
        token: JWT токен

    Returns:
        UUID пользователя (строка) или None при ошибке
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        return user_id
    except JWTError:
        return None
