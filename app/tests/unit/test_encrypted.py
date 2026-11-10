import json
from typing import Any, cast

from cryptography.fernet import Fernet

from app.core.config import settings
from app.models.encrypted import Encrypted


def test_encrypted_roundtrip() -> None:
    encrypted = Encrypted(settings.ENCRYPTION_KEY)
    value = {"card_number": "4111111111111111", "expiration_date": "2030-12-31"}

    token = encrypted.process_bind_param(value, cast(Any, None))
    assert token is not None
    assert encrypted.process_result_value(token, cast(Any, None)) == value


def test_encrypted_serializes_json_not_pickle() -> None:
    encrypted = Encrypted(settings.ENCRYPTION_KEY)
    token = encrypted.process_bind_param({"card_number": "4111"}, cast(Any, None))
    assert token is not None

    fernet = Fernet(settings.ENCRYPTION_KEY.encode())
    raw = fernet.decrypt(token.encode())
    assert json.loads(raw) == {"card_number": "4111"}
