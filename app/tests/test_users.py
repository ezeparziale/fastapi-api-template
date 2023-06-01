import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app import schemas
from app.core.config import settings
from app.models import User


def test_create_user(client: TestClient):
    res = client.post(
        "/api/v1/users/", json={"email": "abc1@test.com", "password": "abc123"}
    )
    print(res.json())
    new_user = schemas.UserOut(**res.json())
    assert new_user.email == "abc1@test.com"
    assert res.status_code == 201


def test_login(client: TestClient, test_user: User):
    res = client.post(
        "/api/v1/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    print(res.json())
    login_res = schemas.Token(**res.json())
    payload = jwt.decode(
        login_res.access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    id = payload.get("id")
    assert id == test_user["id"]
    assert login_res.token_type == "bearer"
    assert res.status_code == 200


@pytest.mark.parametrize(
    "email, password, status_code",
    [
        ("wrong_email@test.com", "abc123", 403),
        ("abc1@test.com", "wrong_password", 403),
        ("wrong_email@test.com", "wrong_password", 403),
        (None, "wrong_password", 422),
        ("abc1@test.com", None, 422),
    ],
)
def test_incorrent_login(
    client: TestClient, email: str, password: str, status_code: int
):
    res = client.post("/api/v1/login", data={"username": email, "password": password})

    assert res.status_code == status_code
