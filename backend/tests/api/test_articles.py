"""Тесты API статей."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_articles_empty(client: AsyncClient):
    """Получение пустого списка статей."""
    response = await client.get("/api/v1/articles")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_article_unauthorized(client: AsyncClient):
    """Создание статьи без авторизации."""
    response = await client.post(
        "/api/v1/articles",
        json={
            "slug": "test",
            "title": "Test",
            "description": "Test",
            "content": "# Test",
            "category": "Test",
        },
    )
    # 401 без ключа или 422 если заголовок обязателен
    assert response.status_code in [401, 422]


@pytest.mark.asyncio
async def test_create_and_get_article(
    client: AsyncClient,
    admin_api_key: str,
):
    """Создание и получение статьи."""
    # Создаём
    response = await client.post(
        "/api/v1/articles",
        headers={"X-API-Key": admin_api_key},
        json={
            "slug": "test-article",
            "title": "Тестовая статья",
            "description": "Описание тестовой статьи",
            "content": "# Заголовок\n\nТекст статьи",
            "category": "Тест",
            "is_published": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "test-article"

    # Получаем
    response = await client.get("/api/v1/articles/test-article")
    assert response.status_code == 200
    assert response.json()["title"] == "Тестовая статья"


@pytest.mark.asyncio
async def test_get_article_not_found(client: AsyncClient):
    """Получение несуществующей статьи возвращает 404."""
    response = await client.get("/api/v1/articles/non-existent-slug")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_article(
    client: AsyncClient,
    admin_api_key: str,
):
    """Обновление статьи."""
    # Сначала создаём статью
    await client.post(
        "/api/v1/articles",
        headers={"X-API-Key": admin_api_key},
        json={
            "slug": "update-test",
            "title": "Исходный заголовок",
            "description": "Описание",
            "content": "# Контент",
            "category": "Тест",
            "is_published": True,
        },
    )

    # Обновляем
    response = await client.put(
        "/api/v1/articles/update-test",
        headers={"X-API-Key": admin_api_key},
        json={
            "title": "Обновлённый заголовок",
        },
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Обновлённый заголовок"


@pytest.mark.asyncio
async def test_update_article_unauthorized(client: AsyncClient):
    """Обновление статьи без авторизации."""
    response = await client.put(
        "/api/v1/articles/some-slug",
        json={"title": "New Title"},
    )
    assert response.status_code in [401, 422]


@pytest.mark.asyncio
async def test_delete_article(
    client: AsyncClient,
    admin_api_key: str,
):
    """Удаление статьи."""
    # Создаём
    await client.post(
        "/api/v1/articles",
        headers={"X-API-Key": admin_api_key},
        json={
            "slug": "delete-test",
            "title": "Для удаления",
            "description": "Описание",
            "content": "# Контент",
            "category": "Тест",
            "is_published": True,
        },
    )

    # Удаляем
    response = await client.delete(
        "/api/v1/articles/delete-test",
        headers={"X-API-Key": admin_api_key},
    )
    assert response.status_code == 204

    # Проверяем что удалена
    response = await client.get("/api/v1/articles/delete-test")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_article_unauthorized(client: AsyncClient):
    """Удаление статьи без авторизации."""
    response = await client.delete("/api/v1/articles/some-slug")
    assert response.status_code in [401, 422]


@pytest.mark.asyncio
async def test_create_duplicate_slug(
    client: AsyncClient,
    admin_api_key: str,
):
    """Создание статьи с дублирующимся slug возвращает 409."""
    article_data = {
        "slug": "duplicate-slug",
        "title": "Первая статья",
        "description": "Описание",
        "content": "# Контент",
        "category": "Тест",
    }

    # Первая статья
    response = await client.post(
        "/api/v1/articles",
        headers={"X-API-Key": admin_api_key},
        json=article_data,
    )
    assert response.status_code == 201

    # Вторая с тем же slug
    response = await client.post(
        "/api/v1/articles",
        headers={"X-API-Key": admin_api_key},
        json=article_data,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_unpublished_article_returns_404(
    client: AsyncClient,
    admin_api_key: str,
):
    """Неопубликованная статья недоступна через публичный endpoint."""
    # Создаём неопубликованную статью
    await client.post(
        "/api/v1/articles",
        headers={"X-API-Key": admin_api_key},
        json={
            "slug": "unpublished-article",
            "title": "Скрытая статья",
            "description": "Описание",
            "content": "# Контент",
            "category": "Тест",
            "is_published": False,
        },
    )

    # Пытаемся получить
    response = await client.get("/api/v1/articles/unpublished-article")
    assert response.status_code == 404
