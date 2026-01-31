#!/usr/bin/env python3
"""
Скрипт для работы с API статей KleyKod.

Функции:
- Получение списка статей с сервера
- Локальное кэширование статей
- Проверка дубликатов перед созданием
- Создание новых статей

Использование:
    python scripts/articles_api.py list          # Показать все статьи
    python scripts/articles_api.py sync          # Синхронизировать кэш с сервером
    python scripts/articles_api.py create <file> # Создать статью из JSON файла
    python scripts/articles_api.py check <slug>  # Проверить существует ли статья
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

# Конфигурация
API_BASE_URL = "https://kleykod.ru/api/v1"
CACHE_FILE = Path(__file__).parent.parent / ".cache" / "articles_cache.json"
ENV_FILE = Path(__file__).parent.parent / ".env.local"


def load_api_key() -> str:
    """Загрузить API ключ из .env.local или переменной окружения."""
    # Сначала проверяем переменную окружения
    api_key = os.environ.get("KLEYKOD_ADMIN_API_KEY")
    if api_key:
        return api_key

    # Затем пробуем .env.local
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                if line.startswith("KLEYKOD_ADMIN_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")

    raise ValueError(
        "API ключ не найден. Установите KLEYKOD_ADMIN_API_KEY в переменных окружения "
        "или в файле .env.local"
    )


def load_cache() -> dict:
    """Загрузить кэш статей."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"articles": [], "last_sync": None}


def save_cache(cache: dict) -> None:
    """Сохранить кэш статей."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_articles() -> list[dict]:
    """Получить список статей с сервера."""
    with httpx.Client(timeout=30) as client:
        response = client.get(f"{API_BASE_URL}/articles")
        response.raise_for_status()
        return response.json()


def sync_cache() -> dict:
    """Синхронизировать кэш с сервером."""
    print("Синхронизация с сервером...")
    articles = fetch_articles()
    cache = {
        "articles": articles,
        "last_sync": datetime.now().isoformat(),
    }
    save_cache(cache)
    print(f"Синхронизировано {len(articles)} статей")
    return cache


def get_cached_slugs() -> set[str]:
    """Получить множество slug из кэша."""
    cache = load_cache()
    return {a["slug"] for a in cache.get("articles", [])}


def check_duplicate(slug: str) -> bool:
    """Проверить, существует ли статья с таким slug."""
    # Сначала проверяем кэш
    if slug in get_cached_slugs():
        return True

    # Если нет в кэше, проверяем на сервере
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(f"{API_BASE_URL}/articles/{slug}")
            return response.status_code == 200
    except httpx.HTTPError:
        return False


def create_article(data: dict) -> dict:
    """Создать статью через API."""
    slug = data.get("slug")

    # Проверка дубликата
    if check_duplicate(slug):
        raise ValueError(f"Статья со slug '{slug}' уже существует!")

    api_key = load_api_key()

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{API_BASE_URL}/articles",
            json=data,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        result = response.json()

    # Обновляем кэш
    cache = load_cache()
    cache["articles"].append(
        {
            "slug": result["slug"],
            "title": result["title"],
            "description": result["description"],
            "category": result["category"],
            "reading_time": result["reading_time"],
            "created_at": result["created_at"],
        }
    )
    save_cache(cache)

    return result


def list_articles() -> None:
    """Показать список статей из кэша."""
    cache = load_cache()
    articles = cache.get("articles", [])

    if not articles:
        print("Кэш пуст. Выполните 'sync' для загрузки статей.")
        return

    print(f"\nСтатей в кэше: {len(articles)}")
    print(f"Последняя синхронизация: {cache.get('last_sync', 'никогда')}\n")
    print("-" * 80)

    for i, article in enumerate(articles, 1):
        print(f"{i}. [{article['category']}] {article['title']}")
        print(f"   slug: {article['slug']}")
        print(f"   {article['description'][:60]}...")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "list":
        list_articles()

    elif command == "sync":
        sync_cache()

    elif command == "check":
        if len(sys.argv) < 3:
            print("Использование: articles_api.py check <slug>")
            sys.exit(1)
        slug = sys.argv[2]
        exists = check_duplicate(slug)
        if exists:
            print(f"Статья '{slug}' существует")
        else:
            print(f"Статья '{slug}' НЕ существует — можно создавать")

    elif command == "create":
        if len(sys.argv) < 3:
            print("Использование: articles_api.py create <file.json>")
            sys.exit(1)
        filepath = Path(sys.argv[2])
        if not filepath.exists():
            print(f"Файл не найден: {filepath}")
            sys.exit(1)

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        try:
            result = create_article(data)
            print(f"Статья создана: {result['slug']}")
            print(f"URL: https://kleykod.ru/articles/{result['slug']}")
        except ValueError as e:
            print(f"Ошибка: {e}")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            print(f"Ошибка API: {e.response.status_code} - {e.response.text}")
            sys.exit(1)

    else:
        print(f"Неизвестная команда: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
