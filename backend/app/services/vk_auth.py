"""
Функции для работы с VK ID API.

Обмен authorization code на access_token и получение данных пользователя.
Используется для VK One Tap авторизации на сайте.
"""

import httpx
from fastapi import HTTPException, status

from app.config import get_settings

# VK ID API endpoints (новый API, не oauth.vk.com)
VK_TOKEN_URL = "https://id.vk.com/oauth2/auth"
VK_USER_INFO_URL = "https://id.vk.com/oauth2/user_info"


async def exchange_vk_code(code: str, device_id: str) -> dict:
    """
    Обмен authorization code на access_token.

    VK ID использует endpoint https://id.vk.com/oauth2/auth
    (не oauth.vk.com как в старом API).

    Args:
        code: Authorization code от VK One Tap
        device_id: Device ID от VK SDK

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
                "client_secret": settings.vk_client_secret,
                "device_id": device_id,
                "redirect_uri": settings.vk_redirect_uri,
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
