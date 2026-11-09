import logging

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_cache_service
from app.main import app
from app.schemas import APIStatusOut, LivenessOut, ReadinessOut


class FakeCache:
    """Minimal cache double used to control the Redis health status."""

    def __init__(self, healthy: bool) -> None:
        self._healthy = healthy

    async def health_check(self) -> bool:
        """Return the health status configured for the test."""
        return self._healthy


# Test: /health endpoint should return 200 and valid APIStatusOut when healthy
def test_api_health(client: TestClient) -> None:
    res = client.get("/health")

    data = res.json()
    APIStatusOut(**data)
    logging.debug(data)

    assert res.status_code == 200
    assert data["status"] == "healthy"
    assert data["db_status"] == "healthy"


# Test: /health endpoint should return 503 and status 'unhealthy' when DB error occurs
def test_api_health_db_error(client_with_db_error: TestClient) -> None:
    res = client_with_db_error.get("/health")

    data = res.json()
    APIStatusOut(**data)
    logging.debug(data)

    assert res.status_code == 503
    assert data["status"] == "unhealthy"
    assert data["db_status"] == "unhealthy"


# Test: /health/live should return 200 without checking any dependency
def test_api_health_live(client: TestClient) -> None:
    res = client.get("/health/live")

    data = res.json()
    LivenessOut(**data)
    logging.debug(data)

    assert res.status_code == 200
    assert data["status"] == "alive"


# Test: /health/ready reports the cache status but stays ready without Redis
@pytest.mark.parametrize(
    "redis_healthy, expected_redis_status",
    [
        (True, "healthy"),
        (False, "unhealthy"),
    ],
)
def test_api_health_ready(
    client: TestClient,
    redis_healthy: bool,
    expected_redis_status: str,
) -> None:
    app.dependency_overrides[get_cache_service] = lambda: FakeCache(redis_healthy)
    try:
        res = client.get("/health/ready")
    finally:
        app.dependency_overrides.pop(get_cache_service, None)

    data = res.json()
    ReadinessOut(**data)
    logging.debug(data)

    assert res.status_code == 200
    assert data["status"] == "healthy"
    assert data["db_status"] == "healthy"
    assert data["redis_status"] == expected_redis_status


# Test: /health/ready should return 503 when the database is unavailable
def test_api_health_ready_db_error(client_with_db_error: TestClient) -> None:
    app.dependency_overrides[get_cache_service] = lambda: FakeCache(True)
    try:
        res = client_with_db_error.get("/health/ready")
    finally:
        app.dependency_overrides.pop(get_cache_service, None)

    data = res.json()
    ReadinessOut(**data)
    logging.debug(data)

    assert res.status_code == 503
    assert data["status"] == "unhealthy"
    assert data["db_status"] == "unhealthy"
