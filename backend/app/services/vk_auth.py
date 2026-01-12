"""
Функции для работы с VK ID API и VK Mini App.

1. VK One Tap (сайт): обмен authorization code на access_token
2. VK Mini App: проверка подписи launch_params (HMAC-SHA256)
"""

import base64
import hashlib
import hmac
import logging
import time
from urllib.parse import parse_qs, urlencode

import httpx
from fastapi import HTTPException, status

from app.config import get_settings

logger = logging.getLogger(__name__)

# VK ID API endpoints (новый API: id.vk.ru, не id.vk.com!)
VK_TOKEN_URL = "https://id.vk.ru/oauth2/auth"
VK_USER_INFO_URL = "https://id.vk.ru/oauth2/user_info"


async def exchange_vk_code(code: str, device_id: str, code_verifier: str) -> dict:
    """
    Обмен authorization code на access_token с PKCE.

    VK ID использует endpoint https://id.vk.ru/oauth2/auth
    (не oauth.vk.com как в старом API).

    Args:
        code: Authorization code от VK One Tap
        device_id: Device ID от VK SDK
        code_verifier: PKCE code_verifier для верификации

    Returns:
        dict с access_token, user_id, expires_in

    Raises:
        HTTPException: При ошибке обмена
    """
    settings = get_settings()

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            VK_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.vk_id_app_id,
                "device_id": device_id,
                "redirect_uri": settings.vk_redirect_uri,
                "code_verifier": code_verifier,
            },
        )

        if response.status_code != 200:
            error_text = response.text
            print(f"[VK Auth] Token exchange failed: {error_text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Ошибка авторизации VK: {error_text}",
            )

        data = response.json()

        # Проверяем наличие ошибки в ответе
        if "error" in data:
            error_desc = data.get("error_description", data.get("error"))
            print(f"[VK Auth] Token exchange error: {error_desc}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Ошибка VK: {error_desc}",
            )

        # Ответ: { "access_token": "...", "user_id": 123, "expires_in": 86400 }
        return data


async def get_vk_user_info(access_token: str, user_id: int) -> dict:
    """
    Получение данных пользователя через VK ID API.

    Args:
        access_token: Токен доступа VK
        user_id: ID пользователя VK

    Returns:
        dict с id, first_name, last_name пользователя

    Raises:
        HTTPException: При ошибке получения данных
    """
    settings = get_settings()

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            VK_USER_INFO_URL,
            data={
                "access_token": access_token,
                "client_id": settings.vk_id_app_id,
            },
        )

        if response.status_code != 200:
            error_text = response.text
            print(f"[VK Auth] User info failed: {error_text}")
            # Fallback — возвращаем минимальные данные
            return {"id": user_id, "first_name": "VK User", "last_name": ""}

        data = response.json()

        # Проверяем наличие ошибки
        if "error" in data:
            print(f"[VK Auth] User info error: {data}")
            return {"id": user_id, "first_name": "VK User", "last_name": ""}

        # Ответ: { "user": { "id": 123, "first_name": "...", "last_name": "..." } }
        user_data = data.get("user", {})
        return {
            "id": user_data.get("user_id", user_id),
            "first_name": user_data.get("first_name", "VK User"),
            "last_name": user_data.get("last_name", ""),
        }


# === VK Mini App: проверка подписи launch_params ===


def verify_launch_params(
    launch_params: str,
    vk_app_secret: str,
    expected_app_id: int,
    max_age_seconds: int = 86400,
) -> dict | None:
    """
    Проверяет HMAC-SHA256 подпись VK Mini App launch_params.

    Алгоритм проверки согласно документации VK:
    https://dev.vk.com/mini-apps/development/launch-params

    Args:
        launch_params: Query string с параметрами запуска (vk_user_id=123&...&sign=xxx)
        vk_app_secret: Секретный ключ приложения VK
        expected_app_id: Ожидаемый ID приложения (защита от подмены)
        max_age_seconds: Максимальный возраст параметров (защита от replay attack)

    Returns:
        dict с vk_user_id и vk_app_id или None если подпись невалидна
    """
    try:
        params = parse_qs(launch_params, keep_blank_values=True)

        # Извлекаем sign (подпись)
        sign_list = params.pop("sign", [None])
        sign = sign_list[0] if sign_list else None
        if not sign:
            logger.warning("[VK Auth] launch_params без sign")
            return None

        # Собираем только vk_* параметры
        vk_params = {k: v[0] for k, v in params.items() if k.startswith("vk_")}

        # Проверяем vk_app_id
        app_id = int(vk_params.get("vk_app_id", 0))
        if app_id != expected_app_id:
            logger.warning(f"[VK Auth] Неверный vk_app_id: {app_id} != {expected_app_id}")
            return None

        # Проверяем timestamp (защита от replay attack)
        vk_ts = int(vk_params.get("vk_ts", 0))
        if vk_ts:
            age = time.time() - vk_ts
            if age > max_age_seconds:
                logger.warning(f"[VK Auth] launch_params устарели: {age:.0f}s > {max_age_seconds}s")
                return None

        # Сортируем параметры по ключу и кодируем
        sorted_params = urlencode(sorted(vk_params.items()))

        # Вычисляем HMAC-SHA256
        secret = hmac.new(
            key=vk_app_secret.encode(),
            msg=sorted_params.encode(),
            digestmod=hashlib.sha256,
        ).digest()

        # base64url без padding (как в VK)
        expected_sign = base64.urlsafe_b64encode(secret).rstrip(b"=").decode()

        # Сравнение без timing attack
        if not hmac.compare_digest(sign, expected_sign):
            logger.warning("[VK Auth] Невалидная подпись launch_params")
            return None

        vk_user_id = int(vk_params.get("vk_user_id", 0))
        if not vk_user_id:
            logger.warning("[VK Auth] vk_user_id отсутствует в launch_params")
            return None

        logger.info(f"[VK Auth] launch_params проверены, user_id={vk_user_id}")
        return {
            "vk_user_id": vk_user_id,
            "vk_app_id": app_id,
        }

    except Exception as e:
        logger.error(f"[VK Auth] Ошибка проверки launch_params: {e}")
        return None


async def verify_vk_access_token(access_token: str) -> dict | None:
    """
    Проверяет VK access_token через VK API (fallback метод).

    Вызывает users.get для получения данных пользователя.
    Используется когда launch_params недоступны.

    Args:
        access_token: Access token VK (от VKWebAppGetAuthToken)

    Returns:
        dict с vk_user_id, first_name, last_name или None при ошибке
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.vk.com/method/users.get",
                params={
                    "access_token": access_token,
                    "v": "5.199",
                    "fields": "first_name,last_name",
                },
            )

        data = response.json()

        if "error" in data:
            error_msg = data["error"].get("error_msg", "Unknown error")
            logger.warning(f"[VK Auth] VK API error: {error_msg}")
            return None

        users = data.get("response", [])
        if not users:
            logger.warning("[VK Auth] VK API вернул пустой ответ")
            return None

        user = users[0]
        vk_user_id = user.get("id")
        if not vk_user_id:
            logger.warning("[VK Auth] VK API не вернул id пользователя")
            return None

        logger.info(f"[VK Auth] access_token проверен, user_id={vk_user_id}")
        return {
            "vk_user_id": vk_user_id,
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
        }

    except Exception as e:
        logger.error(f"[VK Auth] Ошибка проверки access_token: {e}")
        return None
