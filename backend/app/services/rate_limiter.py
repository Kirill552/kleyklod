"""
Rate limiter для API ключей на базе Redis.

Использует sliding window алгоритм.
Лимит: 100 запросов в минуту на один API ключ.
"""

import time

from redis.asyncio import Redis


class RateLimiter:
    """
    Sliding window rate limiter на Redis.

    Хранит timestamps запросов в sorted set.
    При каждом запросе удаляет старые и проверяет количество.
    """

    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_rate_limit(
        self,
        key: str,
        limit: int = 100,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """
        Проверяет лимит запросов.

        Args:
            key: Идентификатор (user_id или api_key_id)
            limit: Максимум запросов в окне
            window_seconds: Размер окна в секундах

        Returns:
            (allowed, remaining, reset_timestamp)
            - allowed: можно ли выполнить запрос
            - remaining: сколько запросов осталось
            - reset_timestamp: когда сбросится лимит
        """
        now = time.time()
        window_start = now - window_seconds
        redis_key = f"ratelimit:{key}"

        pipe = self.redis.pipeline()

        # Удаляем старые записи
        pipe.zremrangebyscore(redis_key, 0, window_start)
        # Добавляем текущий запрос
        pipe.zadd(redis_key, {str(now): now})
        # Считаем запросы в окне
        pipe.zcard(redis_key)
        # Устанавливаем TTL
        pipe.expire(redis_key, window_seconds)

        results = await pipe.execute()
        request_count = results[2]

        allowed = request_count <= limit
        remaining = max(0, limit - request_count)
        reset_timestamp = int(now + window_seconds)

        return allowed, remaining, reset_timestamp

    async def get_remaining(
        self,
        key: str,
        limit: int = 100,
        window_seconds: int = 60,
    ) -> tuple[int, int]:
        """
        Получает оставшееся количество запросов (без добавления нового).

        Args:
            key: Идентификатор
            limit: Максимум запросов в окне
            window_seconds: Размер окна в секундах

        Returns:
            (remaining, reset_timestamp)
        """
        now = time.time()
        window_start = now - window_seconds
        redis_key = f"ratelimit:{key}"

        # Удаляем старые записи и считаем
        await self.redis.zremrangebyscore(redis_key, 0, window_start)
        request_count = await self.redis.zcard(redis_key)

        remaining = max(0, limit - request_count)
        reset_timestamp = int(now + window_seconds)

        return remaining, reset_timestamp
