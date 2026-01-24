import logging

from fastapi.testclient import TestClient

from app.schemas import APIStatus


# Test: /health endpoint should return 200 and valid APIStatus when healthy
def test_api_health(client: TestClient) -> None:
    res = client.get("/health")

    def validate(data) -> APIStatus:
        return APIStatus(**data)

    data = res.json()
    validate(data)
    logging.debug(data)

    assert res.status_code == 200


# Test: /health endpoint should return 200 and db_status 'Unhealthy'
# when DB error occurs
def test_api_health_db_error(client_with_db_error: TestClient) -> None:
    res = client_with_db_error.get("/health")

    def validate(data) -> APIStatus:
        return APIStatus(**data)

    data = res.json()
    validate(data)
    logging.debug(data)

    assert res.status_code == 200
    assert data["db_status"] == "Unhealthy"
