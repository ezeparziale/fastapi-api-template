import json
from typing import Any, cast

from loguru import logger
from redis.asyncio import Redis

from app.core.config import settings


class CacheService:
    redis_client: Redis = Redis(
        host=settings.REDIS_HOSTNAME,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )

    def __init__(
        self, endpoint_path: str | None = None, enabled: bool = settings.CACHE_ENABLED
    ):
        self.redis = self.redis_client
        self.endpoint_path = endpoint_path
        self._enabled = enabled

    @property
    def is_enabled(self) -> bool:
        """Check if caching is enabled globally and for this specific endpoint."""
        if not self._enabled:
            logger.debug("Caching is globally disabled.")
            return False

        if (
            self.endpoint_path
            and self.endpoint_path in settings.CACHE_DISABLED_ENDPOINTS
        ):
            logger.debug(f"Caching is disabled for endpoint: {self.endpoint_path}")
            return False

        return True

    async def get(self, key: str) -> Any | None:
        """Get a value from cache. Returns None if disabled or key not found."""
        if not self.is_enabled:
            return None

        try:
            data = await self.redis.get(key)
            if data:
                logger.info(f"Cache HIT for key: {key}")
                return json.loads(data)
            logger.info(f"Cache MISS for key: {key}")
        except Exception as e:
            logger.error(f"Error retrieving from cache ({key}): {e}")
        return None

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        """Set a value in cache. Does nothing if caching is disabled."""
        if not self.is_enabled:
            return False

        try:
            serialized_value = json.dumps(value)
            result = await self.redis.set(key, serialized_value, ex=ex)
            if result:
                logger.info(f"Cache SET successful for key: {key} (TTL: {ex}s)")
            return bool(result)
        except Exception as e:
            logger.error(f"Error saving to cache ({key}): {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a specific key from cache."""
        try:
            result = await self.redis.delete(key)
            if result:
                logger.info(f"Cache DELETE for key: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting from cache ({key}): {e}")
            return False

    async def clear_all(self) -> bool:
        """Clear all cache data (FLUSHDB)."""
        try:
            logger.warning("Full cache clear triggered (FLUSHDB)")
            return bool(await self.redis.flushdb())
        except Exception as e:
            logger.error(f"Error clearing full cache: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> bool:
        """Delete all keys matching a specific pattern (e.g., 'posts:*')."""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                logger.info(
                    f"Clearing cache by pattern '{pattern}'. Found {len(keys)} keys."
                )
                return bool(await self.redis.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"Error clearing cache by pattern ({pattern}): {e}")
            return False

    async def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            if await cast(Any, self.redis.ping()):
                logger.debug("Redis connection is healthy.")
                return True
            return False
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
