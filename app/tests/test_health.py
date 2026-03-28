import logging

from fastapi.testclient import TestClient

from app.schemas import APIStatus


# Test: /health endpoint should return 200 and valid APIStatus when healthy
def test_api_health(client: TestClient) -> None:
    res = client.get("/health")

    data = res.json()
    APIStatus(**data)
    logging.debug(data)

    assert res.status_code == 200
    assert data["status"] == "healthy"
    assert data["db_status"] == "healthy"


# Test: /health endpoint should return 503 and status 'unhealthy' when DB error occurs
def test_api_health_db_error(client_with_db_error: TestClient) -> None:
    res = client_with_db_error.get("/health")

    data = res.json()
    APIStatus(**data)
    logging.debug(data)

    assert res.status_code == 503
    assert data["status"] == "unhealthy"
    assert data["db_status"] == "unhealthy"
