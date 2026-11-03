import asyncio
import time
from collections.abc import Generator
from typing import Any, cast

import pytest

from app.services.cache import CacheService


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.fail = False
        self.ping_result: Any = True
        self.ping_error: Exception | None = None

    async def get(self, key: str) -> str | None:
        if self.fail:
            raise RuntimeError("redis down")
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        if self.fail:
            raise RuntimeError("redis down")
        self.store[key] = value
        return True

    async def delete(self, *keys: str) -> int:
        if self.fail:
            raise RuntimeError("redis down")
        deleted = 0
        for key in keys:
            if key in self.store:
                del self.store[key]
                deleted += 1
        return deleted

    async def keys(self, pattern: str) -> list[str]:
        if self.fail:
            raise RuntimeError("redis down")
        prefix = pattern.rstrip("*")
        return [key for key in self.store if key.startswith(prefix)]

    async def flushdb(self) -> bool:
        if self.fail:
            raise RuntimeError("redis down")
        self.store.clear()
        return True

    async def ping(self) -> Any:
        if self.ping_error is not None:
            raise self.ping_error
        return self.ping_result


@pytest.fixture(autouse=True)
def reset_circuit() -> Generator[None]:
    CacheService._consecutive_failures = 0
    CacheService._open_until = 0.0
    yield
    CacheService._consecutive_failures = 0
    CacheService._open_until = 0.0


def make_service(
    redis: FakeRedis | None = None,
    *,
    enabled: bool = True,
    endpoint_path: str | None = None,
) -> CacheService:
    service = CacheService(endpoint_path=endpoint_path, enabled=enabled)
    service.redis = cast(Any, redis or FakeRedis())
    return service


def test_is_enabled_false_when_globally_disabled() -> None:
    assert make_service(enabled=False).is_enabled is False


def test_is_enabled_false_for_disabled_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.cache.settings.CACHE_DISABLED_ENDPOINTS", ["/posts"]
    )

    assert make_service(endpoint_path="/posts").is_enabled is False


def test_is_enabled_true_by_default() -> None:
    assert make_service().is_enabled is True


def test_circuit_allows_call_when_closed() -> None:
    assert CacheService._circuit_allows_call() is True


def test_circuit_allows_probe_after_cooldown() -> None:
    CacheService._consecutive_failures = CacheService.failure_threshold
    CacheService._open_until = time.monotonic() - 1

    assert CacheService._circuit_allows_call() is True
    assert CacheService._open_until == 0.0
    assert CacheService._consecutive_failures == CacheService.failure_threshold - 1


def test_circuit_blocks_while_open() -> None:
    CacheService._open_until = time.monotonic() + 60

    assert CacheService._circuit_allows_call() is False


def test_record_failure_opens_circuit() -> None:
    CacheService._consecutive_failures = CacheService.failure_threshold - 1

    CacheService._record_failure("test")

    assert CacheService._open_until > 0.0


def test_record_success_resets_circuit() -> None:
    CacheService._consecutive_failures = 2
    CacheService._open_until = time.monotonic() + 60

    CacheService._record_success()

    assert CacheService._consecutive_failures == 0
    assert CacheService._open_until == 0.0


def test_get_returns_cached_value_and_none_for_miss() -> None:
    service = make_service()

    assert asyncio.run(service.set("key", {"a": 1}, ex=10)) is True
    assert asyncio.run(service.get("key")) == {"a": 1}
    assert asyncio.run(service.get("missing")) is None


def test_get_and_set_when_disabled() -> None:
    service = make_service(enabled=False)

    assert asyncio.run(service.get("key")) is None
    assert asyncio.run(service.set("key", "value")) is False


def test_get_returns_none_on_redis_failure() -> None:
    redis = FakeRedis()
    redis.fail = True

    assert asyncio.run(make_service(redis).get("key")) is None


def test_write_operations_return_false_on_redis_failure() -> None:
    redis = FakeRedis()
    redis.fail = True
    service = make_service(redis)

    assert asyncio.run(service.set("key", "value")) is False
    assert asyncio.run(service.delete("key")) is False
    assert asyncio.run(service.clear_all()) is False
    assert asyncio.run(service.clear_pattern("posts:*")) is False


def test_delete_returns_true_only_when_key_existed() -> None:
    service = make_service()

    asyncio.run(service.set("key", "value"))

    assert asyncio.run(service.delete("key")) is True
    assert asyncio.run(service.delete("missing")) is False


def test_clear_all_flushes_store() -> None:
    redis = FakeRedis()
    service = make_service(redis)
    asyncio.run(service.set("key", "value"))

    assert asyncio.run(service.clear_all()) is True
    assert redis.store == {}


def test_clear_pattern_without_matches_returns_true() -> None:
    assert asyncio.run(make_service().clear_pattern("posts:*")) is True


def test_clear_pattern_deletes_matching_keys() -> None:
    redis = FakeRedis()
    service = make_service(redis)
    asyncio.run(service.set("posts:1", "a"))
    asyncio.run(service.set("posts:2", "b"))
    asyncio.run(service.set("users:1", "c"))

    assert asyncio.run(service.clear_pattern("posts:*")) is True
    assert list(redis.store) == ["users:1"]


def test_execute_skips_when_circuit_open() -> None:
    CacheService._open_until = time.monotonic() + 60

    assert asyncio.run(make_service().get("key")) is None


def test_health_check_success() -> None:
    assert asyncio.run(make_service().health_check()) is True


def test_health_check_false_when_ping_fails() -> None:
    redis = FakeRedis()
    redis.ping_result = False

    assert asyncio.run(make_service(redis).health_check()) is False


def test_health_check_false_on_exception() -> None:
    redis = FakeRedis()
    redis.ping_error = RuntimeError("redis down")

    assert asyncio.run(make_service(redis).health_check()) is False
