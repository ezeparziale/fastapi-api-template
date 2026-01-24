from unittest.mock import AsyncMock, patch

import pytest
from authlib.jose import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import User
from app.schemas import Token


# Test: Login with correct credentials should return a valid token
def test_login(client: TestClient, test_user: User) -> None:
    # When: a POST request is made to the login endpoint with correct credentials
    res = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": test_user.password},
    )

    # Then: the response should be successful (200 OK)
    assert res.status_code == 200

    # And: the response body should contain a valid token
    login_res = Token(**res.json())
    assert login_res.token_type == "bearer"

    # And: the token payload should contain the correct user ID
    payload = jwt.decode(login_res.access_token, settings.SECRET_KEY)
    user_id = payload.get("sub")
    assert user_id == test_user.id


# Test: Login with incorrect credentials or missing fields should fail
@pytest.mark.parametrize(
    "email, password, status_code",
    [
        # ("wrong_email@test.com", "abc123", 403),  # Non-existent user
        ("abc1@test.com", "wrong_password", 403),  # Correct user, wrong password
        (
            "wrong_email@test.com",
            "wrong_password",
            403,
        ),  # Non-existent user and wrong password
        (None, "wrong_password", 422),  # Missing email
        ("abc1@test.com", None, 422),  # Missing password
    ],
)
@pytest.mark.usefixtures("test_user")
def test_incorrect_login(
    client: TestClient,
    email: str | None,
    password: str | None,
    status_code: int,
) -> None:
    # Given: login data, which may be incorrect or incomplete
    data = {}
    if email is not None:
        data["username"] = email
    if password is not None:
        data["password"] = password

    # When: a POST request is made to the login endpoint
    res = client.post("/api/v1/auth/login", data=data)

    # Then: the response status code should match the
    # expected status code for the scenario
    assert res.status_code == status_code


# --- Google OAuth Tests ---


def test_google_login_redirect(client: TestClient) -> None:
    # When: a GET request is made to the Google login endpoint
    response = client.get("/api/v1/auth/login/google", follow_redirects=False)

    # Then: the response should be a temporary redirect (302)
    assert response.status_code == 302

    # And: the 'location' header should point to the Google OAuth URL
    assert "location" in response.headers
    location_url = response.headers["location"]
    assert "accounts.google.com/o/oauth2/v2/auth" in location_url


def test_google_auth_callback_success(client: TestClient, test_user: User) -> None:
    # Given: A mock for the Google OAuth authorize_access_token method
    # that returns a valid user info payload.
    with patch(
        "app.core.oauth.oauth.google.authorize_access_token",
        new_callable=AsyncMock,
        return_value={"userinfo": {"email": test_user.email}},
    ) as mock_authorize:
        # When: a GET request is made to the Google auth callback endpoint
        response = client.get("/api/v1/auth/google")

        # Then: the response should be successful (200 OK)
        assert response.status_code == 200
        login_res = Token(**response.json())
        assert login_res.token_type == "bearer"
        payload = jwt.decode(login_res.access_token, settings.SECRET_KEY)
        assert payload.get("sub") == test_user.id
        mock_authorize.assert_awaited_once()


def test_google_auth_callback_user_not_found(client: TestClient) -> None:
    # Given: A mock for a non-existent user's email
    with patch(
        "app.core.oauth.oauth.google.authorize_access_token",
        new_callable=AsyncMock,
        return_value={"userinfo": {"email": "nonexistent@user.com"}},
    ) as mock_authorize:
        # When: a GET request is made to the Google auth callback endpoint
        response = client.get("/api/v1/auth/google")

        # Then: the response should be 403 Forbidden
        assert response.status_code == 403
        assert response.json() == {"detail": "Invalid Credentials"}
        mock_authorize.assert_awaited_once()
