"""
Временное хранилище файлов на Redis.

Шарится между всеми workers uvicorn.
"""

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

        # Сохраняем metadata как JSON + data как bytes
        metadata = json.dumps({"filename": filename, "content_type": content_type})

        pipe = self._redis.pipeline()
        pipe.hset(key, mapping={"metadata": metadata, "data": data})
        pipe.expire(key, ttl_seconds)
        await pipe.execute()

    async def get(self, file_id: str) -> StoredFile | None:
        """Получить файл из Redis."""
        key = f"{self.KEY_PREFIX}{file_id}"

        result = await self._redis.hgetall(key)
        if not result:
            return None

        try:
            metadata = json.loads(result[b"metadata"].decode())
            return StoredFile(
                data=result[b"data"],
                filename=metadata["filename"],
                content_type=metadata["content_type"],
            )
        except (KeyError, json.JSONDecodeError) as e:
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
