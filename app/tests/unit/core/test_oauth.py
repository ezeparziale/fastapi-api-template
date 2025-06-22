from unittest.mock import MagicMock

import pytest
from authlib.jose.errors import BadSignatureError, ExpiredTokenError
from fastapi import HTTPException, status

from app.core import oauth


# Mock settings values
@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    monkeypatch.setattr(oauth, "SECRET_KEY", "testsecret")
    monkeypatch.setattr(oauth, "ALGORITHM", "HS256")
    monkeypatch.setattr(oauth, "ACCESS_TOKEN_EXPIRE_MINUTES", 15)


# Test create_access_token returns a valid JWT string
def test_create_access_token_returns_jwt(monkeypatch):
    # Patch jwt.encode to return bytes
    monkeypatch.setattr(oauth.jwt, "encode", lambda **kwargs: b"token123")
    data = {"sub": 1}
    token = oauth.create_access_token(data)
    assert token == "token123"


# Test get_current_user returns user when token is valid and user exists
def test_get_current_user_success(monkeypatch):
    # Mock jwt.decode to return a mock object that can be validated and queried
    mock_payload = MagicMock()
    mock_payload.get.return_value = 1  # Mocks payload.get('sub', None)
    monkeypatch.setattr(oauth.jwt, "decode", lambda token, key: mock_payload)

    # Mock TokenData
    monkeypatch.setattr(oauth, "TokenData", lambda id: MagicMock(id=id))
    # Mock User and db session
    mock_user = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = mock_user
    mock_execute = MagicMock()
    mock_execute.scalars.return_value = mock_scalars
    mock_db = MagicMock()
    mock_db.execute.return_value = mock_execute
    # Call get_current_user
    result = oauth.get_current_user(token="sometoken", db=mock_db)
    assert result is mock_user
    mock_payload.validate.assert_called_once()


# Test get_current_user raises HTTPException if token is invalid (BadSignatureError)
def test_get_current_user_invalid_token(monkeypatch):
    # Patch jwt.decode to raise BadSignatureError
    monkeypatch.setattr(
        oauth.jwt,
        "decode",
        lambda token, key: (_ for _ in ()).throw(BadSignatureError("Invalid token")),
    )
    mock_db = MagicMock()
    with pytest.raises(HTTPException) as excinfo:
        oauth.get_current_user(token="badtoken", db=mock_db)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED


# Test get_current_user raises HTTPException if sub is missing in payload
def test_get_current_user_missing_sub(monkeypatch):
    mock_payload = MagicMock()
    mock_payload.get.return_value = None  # Mocks payload.get('sub', None) -> None
    monkeypatch.setattr(oauth.jwt, "decode", lambda token, key: mock_payload)

    mock_db = MagicMock()
    with pytest.raises(HTTPException) as excinfo:
        oauth.get_current_user(token="token", db=mock_db)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    mock_payload.validate.assert_called_once()


# Test get_current_user raises HTTPException for expired token
def test_get_current_user_expired_token(monkeypatch):
    # Mock jwt.decode to return a payload
    mock_payload = MagicMock()
    # Mock that validate() raises ExpiredTokenError
    mock_payload.validate.side_effect = ExpiredTokenError()
    monkeypatch.setattr(oauth.jwt, "decode", lambda token, key: mock_payload)

    mock_db = MagicMock()
    with pytest.raises(HTTPException) as excinfo:
        oauth.get_current_user(token="expiredtoken", db=mock_db)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    mock_payload.validate.assert_called_once()


# # Test get_current_user raises HTTPException if user not found in db
def test_get_current_user_user_not_found(monkeypatch):
    # Mock jwt.decode to return a mock object
    mock_payload = MagicMock()
    mock_payload.get.return_value = 1
    monkeypatch.setattr(oauth.jwt, "decode", lambda token, key: mock_payload)
    # Mock TokenData to return an object with id
    monkeypatch.setattr(oauth, "TokenData", lambda id: MagicMock(id=id))
    # Mock db session and scalars().first() chain
    mock_user = None
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = mock_user
    mock_execute = MagicMock()
    mock_execute.scalars.return_value = mock_scalars
    mock_db = MagicMock()
    mock_db.execute.return_value = mock_execute
    # Assert HTTPException is raised when user is not found
    with pytest.raises(HTTPException) as excinfo:
        oauth.get_current_user(token="token", db=mock_db)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    mock_payload.validate.assert_called_once()
