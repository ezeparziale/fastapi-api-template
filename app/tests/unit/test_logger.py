import logging
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import pytest
from loguru import logger

from app.logger import InterceptHandler, setup_logging, success_to_info_patcher


def test_success_to_info_patcher_converts_success_level() -> None:
    record = cast(Any, {"level": SimpleNamespace(name="SUCCESS", no=25, icon="✅")})

    success_to_info_patcher(record)

    assert record["level"].name == "INFO"
    assert record["level"].no == logger.level("INFO").no
    assert record["level"].icon == logger.level("INFO").icon


def test_intercept_handler_emits_known_level() -> None:
    handler = InterceptHandler()
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", None, None)

    handler.emit(record)


def test_intercept_handler_uses_level_number_for_unknown_level() -> None:
    handler = InterceptHandler()
    record = logging.LogRecord("test", 5, __file__, 1, "hello", None, None)
    record.levelname = "CUSTOM"

    handler.emit(record)


def test_intercept_handler_handles_missing_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler = InterceptHandler()
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", None, None)
    fake_sys = SimpleNamespace(_getframe=Mock(side_effect=ValueError))
    monkeypatch.setattr("app.logger.sys", fake_sys)

    handler.emit(record)


def test_setup_logging_configures_patcher_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_logger = Mock()
    monkeypatch.setattr("app.logger.logger", mock_logger)
    monkeypatch.setattr("app.logger.settings.ENVIRONMENT", "production")
    monkeypatch.setattr("app.logger.dictConfig", Mock())
    monkeypatch.setattr("app.logger.logging.basicConfig", Mock())

    setup_logging()

    mock_logger.configure.assert_called_once_with(patcher=success_to_info_patcher)
