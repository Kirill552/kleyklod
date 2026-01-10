"""
Кэширование результатов парсинга PDF в Redis.

Ключевая оптимизация: повторный парсинг того же PDF файла мгновенный.
"""

import hashlib
import json
import logging

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# TTL кэша — 1 час (достаточно для сессии пользователя)
CACHE_TTL = 3600


class ParseCache:
    """
    Кэш результатов парсинга PDF по MD5 хэшу файла.

    Используется для мгновенного повторного доступа к уже распарсенным PDF.
    """

    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "parse_cache:"

    def _get_key(self, file_hash: str) -> str:
        """Формирует Redis ключ для кэша."""
        return f"{self.prefix}{file_hash}"

    @staticmethod
    def compute_hash(file_bytes: bytes) -> str:
        """Вычисляет MD5 хэш файла."""
        return hashlib.md5(file_bytes).hexdigest()

    async def get(self, file_hash: str) -> list[str] | None:
        """
        Получить закэшированные коды по хэшу файла.

        Args:
            file_hash: MD5 хэш PDF файла

        Returns:
            Список кодов или None если кэш пустой
        """
        key = self._get_key(file_hash)
        try:
            cached = await self.redis.get(key)
            if cached:
                logger.info(f"Кэш HIT: {file_hash[:8]}...")
                return json.loads(cached)
            logger.debug(f"Кэш MISS: {file_hash[:8]}...")
            return None
        except Exception as e:
            logger.warning(f"Ошибка чтения кэша: {e}")
            return None

    async def set(self, file_hash: str, codes: list[str]) -> None:
        """
        Сохранить коды в кэш.

        Args:
            file_hash: MD5 хэш PDF файла
            codes: Список извлечённых кодов
        """
        key = self._get_key(file_hash)
        try:
            await self.redis.set(key, json.dumps(codes), ex=CACHE_TTL)
            logger.info(f"Кэш SET: {file_hash[:8]}... ({len(codes)} кодов, TTL={CACHE_TTL}s)")
        except Exception as e:
            logger.warning(f"Ошибка записи в кэш: {e}")

    async def delete(self, file_hash: str) -> None:
        """Удалить запись из кэша."""
        key = self._get_key(file_hash)
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Ошибка удаления из кэша: {e}")
