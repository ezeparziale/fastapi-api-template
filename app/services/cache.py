import json
import time
from collections.abc import Awaitable, Callable
from typing import Any, ClassVar, cast

from loguru import logger
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff

from app.core.config import settings

# Returned by _execute when the command could not reach Redis, so callers can
# tell a failure apart from a legitimate cache miss.
_FAILED = object()


class CacheService:
    redis_client: Redis = Redis(
        host=settings.REDIS_HOSTNAME,
        port=settings.REDIS_PORT,
        decode_responses=True,
        # Without these, redis-py retries 10 times with backoff and a 5s
        # timeout each: up to ~65s per command on an unreachable Redis.
        socket_connect_timeout=settings.CACHE_CONNECT_TIMEOUT,
        socket_timeout=settings.CACHE_TIMEOUT,
        retry=Retry(NoBackoff(), 0),
        retry_on_error=[],
    )

    failure_threshold: ClassVar[int] = settings.CACHE_FAILURE_THRESHOLD
    reset_timeout: ClassVar[float] = settings.CACHE_RESET_TIMEOUT
    # Circuit breaker state, shared by every instance like the client itself.
    _consecutive_failures: ClassVar[int] = 0
    _open_until: ClassVar[float] = 0.0

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

    @classmethod
    def _circuit_allows_call(cls) -> bool:
        """Return False while the circuit is open, so requests skip Redis."""
        if not cls._open_until:
            return True

        if time.monotonic() >= cls._open_until:
            # Cooldown elapsed: half-open, let one probe through. A single
            # failure puts us straight back to open.
            cls._open_until = 0.0
            cls._consecutive_failures = cls.failure_threshold - 1
            logger.warning("Cache circuit half-open, allowing a probe")
            return True

        return False

    @classmethod
    def _record_failure(cls, reason: str) -> None:
        cls._consecutive_failures += 1
        if cls._consecutive_failures >= cls.failure_threshold:
            cls._open_until = time.monotonic() + cls.reset_timeout
            logger.error(
                f"Cache circuit opened for {cls.reset_timeout}s after "
                f"{cls._consecutive_failures} consecutive failures ({reason})"
            )

    @classmethod
    def _record_success(cls) -> None:
        if cls._consecutive_failures:
            logger.info("Cache circuit closed, connection recovered")
        cls._consecutive_failures = 0
        cls._open_until = 0.0

    async def _execute(
        self, description: str, command: Callable[[], Awaitable[Any]]
    ) -> Any:
        """Run a Redis command, failing fast and short-circuiting when open."""
        if not self.is_enabled:
            return _FAILED

        if not self._circuit_allows_call():
            logger.warning(f"Cache circuit open, skipping {description}")
            return _FAILED

        try:
            result = await command()
        except Exception as e:
            self._record_failure(f"{description}: {e}")
            logger.error(f"Error {description}: {e}")
            return _FAILED

        self._record_success()
        return result

    @staticmethod
    def _as_bool(result: Any) -> bool:
        return result is not _FAILED and bool(result)

    async def get(self, key: str) -> Any | None:
        """Get a value from cache. Returns None if disabled or key not found."""
        data = await self._execute(
            f"retrieving from cache ({key})", lambda: self.redis.get(key)
        )
        if data is _FAILED:
            return None

        if data:
            logger.info(f"Cache HIT for key: {key}")
            return json.loads(data)
        logger.info(f"Cache MISS for key: {key}")
        return None

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        """Set a value in cache. Does nothing if caching is disabled."""
        if not self.is_enabled:
            return False

        serialized_value = json.dumps(value)
        result = await self._execute(
            f"saving to cache ({key})",
            lambda: self.redis.set(key, serialized_value, ex=ex),
        )
        if self._as_bool(result):
            logger.info(f"Cache SET successful for key: {key} (TTL: {ex}s)")
        return self._as_bool(result)

    async def delete(self, key: str) -> bool:
        """Delete a specific key from cache."""
        result = await self._execute(
            f"deleting from cache ({key})", lambda: self.redis.delete(key)
        )
        if self._as_bool(result):
            logger.info(f"Cache DELETE for key: {key}")
        return self._as_bool(result)

    async def clear_all(self) -> bool:
        """Clear all cache data (FLUSHDB)."""
        logger.warning("Full cache clear triggered (FLUSHDB)")
        result = await self._execute(
            "clearing full cache", lambda: self.redis.flushdb()
        )
        return self._as_bool(result)

    async def clear_pattern(self, pattern: str) -> bool:
        """Delete all keys matching a specific pattern (e.g., 'posts:*')."""
        keys = await self._execute(
            f"clearing cache by pattern ({pattern})", lambda: self.redis.keys(pattern)
        )
        if keys is _FAILED:
            return False

        if not keys:
            return True

        logger.info(f"Clearing cache by pattern '{pattern}'. Found {len(keys)} keys.")
        deleted = await self._execute(
            f"deleting {len(keys)} keys of pattern '{pattern}'",
            lambda: self.redis.delete(*keys),
        )
        return self._as_bool(deleted)

    async def health_check(self) -> bool:
        """Check if Redis connection is healthy. Bypasses the circuit breaker."""
        try:
            if await cast(Any, self.redis.ping()):
                logger.debug("Redis connection is healthy.")
                return True
            return False
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
