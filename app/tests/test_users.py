import pytest
from fastapi.testclient import TestClient

from app.models import User
from app.schemas import UserOut


# Test: Get all users should return 200 and valid user data
def test_get_all_users(
    authorized_client: TestClient, test_user: User, test_user2: User
):
    res = authorized_client.get("/api/v1/users/")

    def validate(user):
        return UserOut(**user)

    data = res.json()
    [validate(item) for item in data]
    print(data)

    assert res.status_code == 200


# Test: Create user with various scenarios (new, existing, invalid email, etc.)
@pytest.mark.parametrize(
    "email, password, status_code",
    [
        ("new_user@test.com", "abc123", 201),
        ("abc1@test.com", "user_exists", 409),
        ("abc1@test", "wrong_email", 422),
        (12345, "wrong_email_type", 422),
        (None, "no_email", 422),
        ("no_password@test.com", None, 422),
    ],
)
def test_create_user(
    client: TestClient,
    email: str | None,
    password: str | None,
    status_code: int,
    test_user: User,  # noqa
):
    data = {"email": email, "password": password}
    res = client.post("/api/v1/users/", json=data)
    print(res.json())
    assert res.status_code == status_code

    if res.status_code == 201:
        new_user = UserOut(**res.json())
        assert new_user.email == email


# Test: Get current user info (me endpoint) should return correct user
def test_get_me(authorized_client: TestClient, test_user: User):
    res = authorized_client.get("/api/v1/users/me")
    print(res.json())
    new_user = UserOut(**res.json())
    assert new_user.email == test_user["email"]
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
):
    params = {"sort_by": fields}
    res = authorized_client.get("/api/v1/users", params=params)
    print(res.json())
    assert res.status_code == status_code


# Test: Search users by email should return the correct user
def test_get_users_search(authorized_client: TestClient, test_user: User):
    params = {"search": test_user["email"]}
    res = authorized_client.get("/api/v1/users", params=params)
    print(res.json())
    assert res.status_code == 200
    data = res.json()
    print(data)
    assert data[0]["email"] == test_user["email"]


# Test: Get user by id should return 200 if exists, 404 if not
@pytest.mark.parametrize(
    "id, status_code",
    [(1, 200), (2, 200), (999, 404)],
)
def test_get_user(
    authorized_client: TestClient,
    id: int,
    status_code: int,
    test_user: User,
    test_user2: User,
):
    res = authorized_client.get(f"/api/v1/users/{id}")
    print(res.json())
    assert res.status_code == status_code

    def validate(user):
        return UserOut(**user)

    if res.status_code == 200:
        data = res.json()
        validate(data)
        print(data)
