"""
Хранение настроек пользователя в Redis.
"""

import json
import logging

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class UserSettings:
    """
    Класс для хранения настроек пользователя в Redis.

    Настройки хранятся в формате JSON с TTL 30 дней.
    """

    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "user_settings:"
        self.ttl = 60 * 60 * 24 * 30  # 30 дней

    def _get_key(self, telegram_id: int) -> str:
        """Получить ключ Redis для пользователя."""
        return f"{self.prefix}{telegram_id}"

    async def get(self, telegram_id: int) -> dict | None:
        """
        Получить настройки пользователя.

        Args:
            telegram_id: ID пользователя Telegram

        Returns:
            dict с настройками или None если не найдены
        """
        key = self._get_key(telegram_id)

        try:
            data = await self.redis.get(key)
            if data is None:
                return None

            return json.loads(data)

        except json.JSONDecodeError as e:
            logger.error(f"[UserSettings] Ошибка парсинга JSON для {telegram_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"[UserSettings] Ошибка получения настроек для {telegram_id}: {e}")
            return None

    async def save(
        self,
        telegram_id: int,
        organization_name: str | None = None,
        inn: str | None = None,
    ) -> None:
        """
        Сохранить настройки пользователя.

        Args:
            telegram_id: ID пользователя Telegram
            organization_name: Название организации
            inn: ИНН организации
        """
        key = self._get_key(telegram_id)

        # Получаем текущие настройки для слияния
        current = await self.get(telegram_id) or {}

        # Обновляем только переданные значения
        if organization_name is not None:
            current["organization_name"] = organization_name
        if inn is not None:
            current["inn"] = inn

        try:
            data = json.dumps(current, ensure_ascii=False)
            await self.redis.set(key, data, ex=self.ttl)
            logger.debug(f"[UserSettings] Настройки сохранены для {telegram_id}")

        except Exception as e:
            logger.error(f"[UserSettings] Ошибка сохранения настроек для {telegram_id}: {e}")
            raise

    async def clear(self, telegram_id: int) -> None:
        """
        Очистить настройки пользователя.

        Args:
            telegram_id: ID пользователя Telegram
        """
        key = self._get_key(telegram_id)

        try:
            await self.redis.delete(key)
            logger.debug(f"[UserSettings] Настройки очищены для {telegram_id}")

        except Exception as e:
            logger.error(f"[UserSettings] Ошибка очистки настроек для {telegram_id}: {e}")
            raise

    async def has_settings(self, telegram_id: int) -> bool:
        """
        Проверить, есть ли сохранённые настройки.

        Args:
            telegram_id: ID пользователя Telegram

        Returns:
            True если настройки существуют
        """
        key = self._get_key(telegram_id)

        try:
            return await self.redis.exists(key) > 0

        except Exception as e:
            logger.error(f"[UserSettings] Ошибка проверки настроек для {telegram_id}: {e}")
            return False


# Глобальные экземпляры
_user_settings: UserSettings | None = None
_redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    """
    Получить Redis клиент (singleton).

    Создаёт подключение к Redis при первом вызове.
    """
    global _redis_client

    if _redis_client is None:
        from bot.config import get_bot_settings

        settings = get_bot_settings()
        _redis_client = Redis.from_url(settings.redis_url)
        logger.debug("[Redis] Создано подключение к Redis")

    return _redis_client


async def get_user_settings_async() -> UserSettings:
    """
    Получить экземпляр UserSettings (async версия).

    Автоматически создаёт Redis подключение если нужно.
    """
    global _user_settings

    if _user_settings is None:
        redis = await get_redis_client()
        _user_settings = UserSettings(redis)

    return _user_settings


def get_user_settings(redis: Redis) -> UserSettings:
    """
    Получить экземпляр UserSettings.

    Args:
        redis: Экземпляр Redis клиента

    Returns:
        UserSettings экземпляр
    """
    global _user_settings
    if _user_settings is None:
        _user_settings = UserSettings(redis)
    return _user_settings
