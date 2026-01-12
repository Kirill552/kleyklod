"""
Временное хранилище файлов на Redis.

Шарится между всеми workers uvicorn.
Данные кодируются в base64 для совместимости с decode_responses=True.
"""

import base64
import json
import logging
from dataclasses import dataclass

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


@dataclass
class StoredFile:
    """Хранимый файл."""

    data: bytes
    filename: str
    content_type: str


class RedisFileStorage:
    """
    Redis-based хранилище файлов.

    Шарится между всеми workers, поддерживает TTL.
    """

    KEY_PREFIX = "file_storage:"

    def __init__(self, redis: Redis):
        self._redis = redis

    async def save(
        self,
        file_id: str,
        data: bytes,
        filename: str = "labels.pdf",
        content_type: str = "application/pdf",
        ttl_seconds: int = 3600,
    ) -> None:
        """Сохранить файл в Redis."""
        key = f"{self.KEY_PREFIX}{file_id}"

        # Кодируем бинарные данные в base64 (для совместимости с decode_responses=True)
        data_b64 = base64.b64encode(data).decode("ascii")

        # Сохраняем всё как JSON
        value = json.dumps(
            {
                "filename": filename,
                "content_type": content_type,
                "data": data_b64,
            }
        )

        await self._redis.setex(key, ttl_seconds, value)

    async def get(self, file_id: str) -> StoredFile | None:
        """Получить файл из Redis."""
        key = f"{self.KEY_PREFIX}{file_id}"

        result = await self._redis.get(key)
        if not result:
            return None

        try:
            parsed = json.loads(result)
            return StoredFile(
                data=base64.b64decode(parsed["data"]),
                filename=parsed["filename"],
                content_type=parsed["content_type"],
            )
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка чтения файла {file_id}: {e}")
            return None

    async def delete(self, file_id: str) -> bool:
        """Удалить файл из Redis."""
        key = f"{self.KEY_PREFIX}{file_id}"
        deleted = await self._redis.delete(key)
        return deleted > 0


# Глобальная переменная для ленивой инициализации
_file_storage: RedisFileStorage | None = None


def get_file_storage(redis: Redis) -> RedisFileStorage:
    """Получить экземпляр file storage."""
    global _file_storage
    if _file_storage is None:
        _file_storage = RedisFileStorage(redis)
    return _file_storage
