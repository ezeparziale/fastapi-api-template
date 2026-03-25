import logging
import sys
import time
from logging.config import dictConfig
from typing import Any, cast

from loguru import logger

from app.core.config import settings


def success_to_info_patcher(record):
    if record["level"].name == "SUCCESS":
        level_info = logger.level("INFO")
        record["level"].name = "INFO"
        record["level"].no = level_info.no
        record["level"].icon = level_info.icon


def setup_logging() -> None:
    # Setting loggers
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": (
                        "%(asctime)s.%(msecs)03d +00:00 | "
                        "%(levelprefix)s %(client_addr)s - "
                        '"%(request_line)s" %(status_code)s'
                    ),
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "use_colors": True,
                },
            },
            "handlers": {
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn.access": {
                    "handlers": ["access"],
                    "propagate": False,
                },
            },
        }
    )

    logging.Formatter.converter = time.gmtime

    for name in ["uvicorn", "uvicorn.error"]:
        logging_logger = logging.getLogger(name)
        logging_logger.handlers = []
        logging_logger.propagate = False

    if settings.ENVIRONMENT == "production":
        logger.configure(patcher=success_to_info_patcher)

    unicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_level = unicorn_logger.level or 20
    uvicorn_level_name = logging.getLevelName(uvicorn_level)

    logger.remove()
    logger.add(
        sys.stdout,
        serialize=True if settings.ENVIRONMENT == "production" else False,
        colorize=True,
        level=uvicorn_level_name,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS!UTC} +00:00 | "
            "<level>{level}</level>: <level>{message}</level>"
        ),
    )

    # Intercept default logging to loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            # Get corresponding Loguru level if it exists.
            try:
                level: str | int = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            depth = 2
            try:
                frame = sys._getframe(depth)
                while frame and frame.f_code.co_filename == logging.__file__:
                    frame = cast(Any, frame.f_back)
                    depth += 1
            except ValueError:
                pass

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for name in ["uvicorn", "uvicorn.error"]:
        u_logger = logging.getLogger(name)
        u_logger.handlers = [InterceptHandler()]
        u_logger.propagate = False
