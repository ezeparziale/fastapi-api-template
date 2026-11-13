import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from joserfc import jwk, jwt
from joserfc.jwk import OctKey

from app.core import oauth


# Mock settings values
@pytest.fixture(autouse=True)
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oauth, "SECRET_KEY", "unit-test-secret-0123456789")
    monkeypatch.setattr(oauth, "ALGORITHM", "HS256")
    monkeypatch.setattr(oauth, "ACCESS_TOKEN_EXPIRE_MINUTES", 15)
    monkeypatch.setattr(oauth, "JWT_ISSUER", "unit-test-issuer")
    monkeypatch.setattr(oauth, "JWT_AUDIENCE", "unit-test-audience")


def build_key(secret: str = "unit-test-secret-0123456789") -> OctKey:
    return jwk.import_key(data=secret, key_type="oct")


def valid_claims(**overrides: Any) -> dict[str, Any]:
    claims: dict[str, Any] = {
        "sub": "1",
        "exp": int(time.time()) + 600,
        "iat": int(time.time()),
        "jti": "unit-test-jti",
        "iss": "unit-test-issuer",
        "aud": "unit-test-audience",
    }
    claims.update(overrides)
    return claims


def mock_db(user: object | None) -> MagicMock:
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = user
    mock_execute = MagicMock()
    mock_execute.scalars.return_value = mock_scalars
    mock_db_obj = MagicMock()
    mock_db_obj.execute.return_value = mock_execute
    return mock_db_obj


# Test create_access_token returns a valid JWT string
def test_create_access_token_returns_jwt() -> None:
    token = oauth.create_access_token(data={"sub": 1})
    assert isinstance(token, str)

    decoded = jwt.decode(value=token, key=build_key(), algorithms=["HS256"])
    assert decoded.claims["sub"] == "1"
    assert decoded.claims["iss"] == "unit-test-issuer"
    assert decoded.claims["aud"] == "unit-test-audience"
    assert "exp" in decoded.claims
    assert "iat" in decoded.claims
    assert "jti" in decoded.claims


# Test get_current_user returns user when token is valid and user exists
def test_get_current_user_success() -> None:
    token = oauth.create_access_token(data={"sub": 1})
    mock_user = MagicMock()
    result = oauth.get_current_user(token=token, db=mock_db(mock_user))
    assert result is mock_user


# Test get_current_user raises HTTPException if token is invalid (BadSignatureError)
def test_get_current_user_invalid_token() -> None:
    token = jwt.encode(
        claims={"sub": "1", "exp": int(time.time()) + 600},
        key=build_key("other-secret-9876543210"),
        header={"alg": "HS256"},
    )
    with pytest.raises(HTTPException) as excinfo:
        oauth.get_current_user(token=token, db=mock_db(MagicMock()))
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED


# Test get_current_user raises HTTPException if sub is missing in payload
def test_get_current_user_missing_sub() -> None:
    claims = valid_claims()
    claims.pop("sub")
    token = jwt.encode(claims=claims, key=build_key(), header={"alg": "HS256"})
    with pytest.raises(HTTPException) as excinfo:
        oauth.get_current_user(token=token, db=mock_db(MagicMock()))
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED


# Test get_current_user raises HTTPException for expired token
def test_get_current_user_expired_token() -> None:
    token = jwt.encode(
        claims=valid_claims(exp=int(time.time()) - 100),
        key=build_key(),
        header={"alg": "HS256"},
    )
    with pytest.raises(HTTPException) as excinfo:
        oauth.get_current_user(token=token, db=mock_db(MagicMock()))
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED


# Test get_current_user rejects tokens with wrong or missing standard claims
@pytest.mark.parametrize(
    "overrides, remove",
    [
        ({"iss": "another-issuer"}, None),
        ({"aud": "another-audience"}, None),
        ({}, "jti"),
        ({}, "iat"),
    ],
)
def test_get_current_user_invalid_standard_claims(
    overrides: dict[str, Any], remove: str | None
) -> None:
    claims = valid_claims(**overrides)
    if remove is not None:
        claims.pop(remove)
    token = jwt.encode(claims=claims, key=build_key(), header={"alg": "HS256"})

    with pytest.raises(HTTPException) as excinfo:
        oauth.get_current_user(token=token, db=mock_db(MagicMock()))
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED


# Test get_current_user raises HTTPException if user not found in db
def test_get_current_user_user_not_found() -> None:
    token = oauth.create_access_token(data={"sub": 1})
    with pytest.raises(HTTPException) as excinfo:
        oauth.get_current_user(token=token, db=mock_db(None))
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
