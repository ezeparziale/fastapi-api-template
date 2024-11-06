from fastapi.testclient import TestClient

from app.schemas import APIStatus


def test_api_health(client: TestClient):
    res = client.get("/health")

    def validate(data):
        return APIStatus(**data)

    data = res.json()
    validate(data)
    print(data)

    assert res.status_code == 200
