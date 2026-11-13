import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.models import User
from app.schemas import UserOut


# Test: Get all users should return 200 and valid user data
@pytest.mark.usefixtures("test_user", "test_user2")
def test_get_all_users(authorized_client: TestClient) -> None:
    res = authorized_client.get("/api/v1/users/")

    def validate(user: dict[str, Any]) -> UserOut:
        return UserOut(**user)

    data = res.json()
    [validate(item) for item in data]
    logging.debug(data)

    assert res.status_code == 200


# Test: Create user with various scenarios (new, existing, invalid email, etc.)
@pytest.mark.parametrize(
    "email, password, status_code",
    [
        ("new_user@test.com", "abc12345", 201),
        ("abc1@test.com", "user_exists", 409),
        ("abc1@test", "wrong_email", 422),
        (12345, "wrong_email_type", 422),
        (None, "no_email", 422),
        ("no_password@test.com", None, 422),
        ("short_password@test.com", "short", 422),
        ("empty_password@test.com", "", 422),
        ("long_password@test.com", "a" * 73, 422),
        ("multibyte_password@test.com", "á" * 40, 422),
        ("max_bytes_password@test.com", "a" * 72, 201),
    ],
)
@pytest.mark.usefixtures("test_user")
def test_create_user(
    client: TestClient,
    email: str | None,
    password: str | None,
    status_code: int,
) -> None:
    data = {"email": email, "password": password}
    res = client.post("/api/v1/users/", json=data)
    logging.debug(res.json())
    assert res.status_code == status_code

    if res.status_code == 201:
        new_user = UserOut(**res.json())
        assert new_user.email == email


# Test: Email is normalized (trimmed and lowercased) when creating a user
def test_create_user_normalizes_email(client: TestClient) -> None:
    res = client.post(
        "/api/v1/users/",
        json={"email": "  Mixed.Case@Example.COM  ", "password": "abc12345"},
    )
    logging.debug(res.json())
    assert res.status_code == 201
    assert res.json()["email"] == "mixed.case@example.com"


# Test: Email uniqueness is case-insensitive
def test_create_user_email_is_case_insensitive(
    client: TestClient, test_user: User
) -> None:
    res = client.post(
        "/api/v1/users/",
        json={"email": test_user.email.upper(), "password": "abc12345"},
    )
    logging.debug(res.json())
    assert res.status_code == 409


# Test: Get current user info (me endpoint) should return correct user
def test_get_me(authorized_client: TestClient, test_user: User) -> None:
    res = authorized_client.get("/api/v1/users/me")
    logging.debug(res.json())
    new_user = UserOut(**res.json())
    assert new_user.email == test_user.email
    assert res.status_code == 200


# Test: Get users sorted by various fields, including invalid ones
@pytest.mark.parametrize(
    "fields, status_code",
    [
        ("id", 200),
        ("-id", 200),
        ("email", 200),
        ("-email", 200),
        ("created_at", 200),
        ("-created_at", 200),
        ("updated_at", 200),
        ("-updated_at", 200),
        ("field_not_exists", 400),
        ("-field_not_exists", 400),
        ("id,email", 200),
        ("-id,email", 200),
    ],
)
def test_get_users_sort_by_fields(
    authorized_client: TestClient, fields: str, status_code: int
) -> None:
    params = {"sort_by": fields}
    res = authorized_client.get("/api/v1/users", params=params)
    logging.debug(res.json())
    assert res.status_code == status_code


# Test: Search users by email should return the correct user
def test_get_users_search(authorized_client: TestClient, test_user: User) -> None:
    params = {"search": test_user.email}
    res = authorized_client.get("/api/v1/users", params=params)
    logging.debug(res.json())
    assert res.status_code == 200
    data = res.json()
    logging.debug(data)
    assert data[0]["email"] == test_user.email


# Test: Pagination pages are based on filtered results, not all users
@pytest.mark.usefixtures("test_user2")
def test_get_users_pagination_pages_uses_filtered_count(
    authorized_client: TestClient, test_user: User
) -> None:
    params: dict[str, str | int] = {"search": test_user.email, "limit": 1}
    res = authorized_client.get("/api/v1/users/", params=params)

    assert res.status_code == 200
    assert res.headers["Total-Count"] == "2"
    assert res.headers["Total-Count-Filtered"] == "1"
    assert res.headers["Pagination-Pages"] == "1"


# Test: Get user by id should return 200 if exists, 404 if not
@pytest.mark.parametrize(
    "id, status_code",
    [(1, 200), (2, 200), (999, 404)],
)
@pytest.mark.usefixtures("test_user", "test_user2")
def test_get_user(
    authorized_client: TestClient,
    id: int,
    status_code: int,
) -> None:
    res = authorized_client.get(f"/api/v1/users/{id}")
    logging.debug(res.json())
    assert res.status_code == status_code

    def validate(user: dict[str, Any]) -> UserOut:
        return UserOut(**user)

    if res.status_code == 200:
        data = res.json()
        validate(data)
        logging.debug(data)
