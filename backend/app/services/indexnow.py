"""
Сервис IndexNow для мгновенного уведомления поисковиков.

IndexNow — протокол для уведомления поисковых систем о новых/обновлённых страницах.
Поддерживается: Yandex, Bing, Seznam, Naver.

Документация: https://www.indexnow.org/documentation
"""

import httpx

from app.config import settings

# Ключ IndexNow (должен совпадать с файлом на сайте)
INDEXNOW_KEY = "kleykod2026indexnow"

# Endpoints поисковых систем
INDEXNOW_ENDPOINTS = [
    "https://yandex.com/indexnow",  # Яндекс — приоритет для ru
    "https://api.indexnow.org/indexnow",  # Bing и партнёры
]


async def notify_indexnow(url: str) -> dict[str, bool]:
    """
    Уведомить поисковики о новой/обновлённой странице.

    Args:
        url: Полный URL страницы (например, https://kleykod.ru/articles/my-article)

    Returns:
        Словарь {endpoint: success} с результатами для каждого поисковика.
    """
    results = {}
    base_url = settings.FRONTEND_URL or "https://kleykod.ru"
    key_location = f"{base_url}/indexnow-key.txt"

    params = {
        "url": url,
        "key": INDEXNOW_KEY,
        "keyLocation": key_location,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in INDEXNOW_ENDPOINTS:
            try:
                response = await client.get(endpoint, params=params)
                # IndexNow возвращает 200 при успехе, 202 если уже в очереди
                results[endpoint] = response.status_code in (200, 202)
            except Exception as e:
                # Не блокируем создание статьи из-за ошибки IndexNow
                print(f"IndexNow error for {endpoint}: {e}")
                results[endpoint] = False

    return results


async def notify_article_indexed(slug: str) -> dict[str, bool]:
    """
    Уведомить поисковики о новой/обновлённой статье.

    Args:
        slug: Slug статьи

    Returns:
        Результаты уведомления.
    """
    base_url = settings.FRONTEND_URL or "https://kleykod.ru"
    article_url = f"{base_url}/articles/{slug}"
    return await notify_indexnow(article_url)
