import pytest

from app.core.config import parse_cors


def test_parse_cors_splits_comma_separated_string() -> None:
    assert parse_cors("http://a.com, http://b.com") == [
        "http://a.com",
        "http://b.com",
    ]


def test_parse_cors_returns_list_as_is() -> None:
    origins = ["http://a.com"]
    assert parse_cors(origins) is origins


def test_parse_cors_returns_json_string_as_is() -> None:
    value = '["http://a.com"]'
    assert parse_cors(value) == value


def test_parse_cors_rejects_invalid_type() -> None:
    with pytest.raises(ValueError):
        parse_cors(1)
