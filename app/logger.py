import logging
import sys
import time
from logging.config import dictConfig

from loguru import logger


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

    unicorn_logger = logging.getLogger("uvicorn.access")

    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS!UTC} +00:00 | "
            "<level>{level}</level>: <level>{message}</level>"
        ),
        level=unicorn_logger.level,
    )
    # logger.level("INFO", color="<green>")

    # Intercept default logging to loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists.
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message.
            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
