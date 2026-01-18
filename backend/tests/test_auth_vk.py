"""
Тесты авторизации через VK.

Покрывает:
- POST /api/v1/auth/vk (авторизация через VK Mini App)
- UserRepository.get_by_vk_id
- UserRepository.create_from_vk
- UserRepository.get_or_create_vk
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ruff: noqa: ARG002


# === Fixtures ===


@pytest.fixture
def mock_redis():
    """Мок Redis для rate limiting."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.exists = AsyncMock(return_value=False)
    return redis


@pytest.fixture
def mock_db_session():
    """Мок AsyncSession для БД."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def test_client(mock_redis, mock_db_session):
    """TestClient с подменёнными зависимостями."""
    from app.db.database import get_db, get_redis
    from app.main import app

    async def override_get_redis():
        return mock_redis

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_redis] = override_get_redis
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    """Мок пользователя из VK."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.vk_user_id = "123456789"
    user.first_name = "Иван"
    user.last_name = "Петров"
    user.plan = "free"
    user.plan_expires_at = None
    user.created_at = datetime.now(UTC)
    return user


# === Тесты endpoint /api/v1/auth/vk ===


class TestVKAuthEndpoint:
    """Тесты endpoint авторизации VK."""

    def test_vk_login_new_user(self, test_client, mock_db_session, mock_user):
        """Успешная авторизация нового пользователя из VK."""
        # Mock: пользователь не найден, создаём нового
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "app.repositories.user_repository.UserRepository.get_or_create_vk",
            new_callable=AsyncMock,
        ) as mock_get_or_create:
            mock_get_or_create.return_value = (mock_user, True)

            response = test_client.post(
                "/api/v1/auth/vk",
                json={
                    "vk_user_id": 123456789,
                    "first_name": "Иван",
                    "last_name": "Петров",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["first_name"] == "Иван"
        assert data["user"]["vk_user_id"] == 123456789

    def test_vk_login_existing_user(self, test_client, mock_db_session, mock_user):
        """Авторизация существующего пользователя из VK."""
        with (
            patch(
                "app.repositories.user_repository.UserRepository.get_or_create_vk",
                new_callable=AsyncMock,
            ) as mock_get_or_create,
            patch(
                "app.repositories.user_repository.UserRepository.update_profile",
                new_callable=AsyncMock,
            ) as mock_update,
        ):
            mock_get_or_create.return_value = (mock_user, False)
            mock_update.return_value = mock_user

            response = test_client.post(
                "/api/v1/auth/vk",
                json={
                    "vk_user_id": 123456789,
                    "first_name": "Иван",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        mock_update.assert_called_once()

    def test_vk_login_missing_vk_user_id(self, test_client):
        """Ошибка при отсутствии vk_user_id."""
        response = test_client.post(
            "/api/v1/auth/vk",
            json={
                "first_name": "Иван",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_vk_login_missing_first_name(self, test_client):
        """Ошибка при отсутствии first_name."""
        response = test_client.post(
            "/api/v1/auth/vk",
            json={
                "vk_user_id": 123456789,
            },
        )

        assert response.status_code == 422  # Validation error


# === Тесты UserRepository ===


class TestUserRepositoryVK:
    """Тесты методов VK в UserRepository."""

    @pytest.mark.asyncio
    async def test_get_by_vk_id_found(self, mock_db_session, mock_user):
        """Поиск пользователя по VK ID — найден."""
        from app.repositories.user_repository import UserRepository

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        repo = UserRepository(mock_db_session)
        user = await repo.get_by_vk_id(123456789)

        assert user is not None
        assert user.vk_user_id == "123456789"

    @pytest.mark.asyncio
    async def test_get_by_vk_id_not_found(self, mock_db_session):
        """Поиск пользователя по VK ID — не найден."""
        from app.repositories.user_repository import UserRepository

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        repo = UserRepository(mock_db_session)
        user = await repo.get_by_vk_id(999999999)

        assert user is None

    @pytest.mark.asyncio
    async def test_create_from_vk(self, mock_db_session):
        """Создание пользователя из VK."""
        from app.repositories.user_repository import UserRepository

        repo = UserRepository(mock_db_session)

        with patch("app.repositories.user_repository.hash_vk_id") as mock_hash:
            mock_hash.return_value = "abc123hash"
            await repo.create_from_vk(
                vk_user_id=123456789,
                first_name="Иван",
                last_name="Петров",
            )

        # Проверяем, что add был вызван
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_vk_creates_new(self, mock_db_session):
        """get_or_create_vk создаёт нового пользователя."""
        from app.repositories.user_repository import UserRepository

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        repo = UserRepository(mock_db_session)

        with patch("app.repositories.user_repository.hash_vk_id") as mock_hash:
            mock_hash.return_value = "abc123hash"
            user, is_new = await repo.get_or_create_vk(
                vk_user_id=123456789,
                first_name="Иван",
            )

        assert is_new is True
        mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_vk_returns_existing(self, mock_db_session, mock_user):
        """get_or_create_vk возвращает существующего пользователя."""
        from app.repositories.user_repository import UserRepository

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        repo = UserRepository(mock_db_session)
        user, is_new = await repo.get_or_create_vk(
            vk_user_id=123456789,
            first_name="Иван",
        )

        assert is_new is False
        assert user == mock_user
        mock_db_session.add.assert_not_called()


# === Тесты hash_vk_id ===


class TestHashVkId:
    """Тесты функции хеширования VK ID."""

    def test_hash_vk_id_deterministic(self):
        """Хеш VK ID детерминистический."""
        from app.utils.encryption import hash_vk_id

        hash1 = hash_vk_id(123456789)
        hash2 = hash_vk_id(123456789)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex

    def test_hash_vk_id_different_for_different_ids(self):
        """Разные ID дают разные хеши."""
        from app.utils.encryption import hash_vk_id

        hash1 = hash_vk_id(123456789)
        hash2 = hash_vk_id(987654321)

        assert hash1 != hash2

    def test_hash_vk_id_works_with_string(self):
        """Хеш работает со строковым ID."""
        from app.utils.encryption import hash_vk_id

        hash1 = hash_vk_id(123456789)
        hash2 = hash_vk_id("123456789")

        assert hash1 == hash2
