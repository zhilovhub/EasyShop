import logging
import logging.config
from dotenv import load_dotenv
import os

from logging import LogRecord


class LokiFilter(logging.Filter):

    def filter(self, record: LogRecord) -> bool:
        print(record.__dict__)
        return True


logger_configuration = {
    "version": 1,
    "formatters": {
        "formatter": {
            "format": "{levelname} {asctime} {filename} {funcName} {msg}",
            "style": "{"
        }
    },
    "filters": {
        "loki_filter": {
            "()": LokiFilter
        }
    },
    "handlers": {
        "console_handler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "formatter",
            "filters": ["loki_filter"]
        }
    },
    "loggers": {
        "debug_logger": {
            "level": "DEBUG",
            "filters": [],
            "handlers": ["console_handler"]
        },
        "release_logger": {
            "level": "DEBUG",
            "filters": [],
            "handlers": ["console_handler"]
        }
    }
}

load_dotenv()
DEBUG = bool(int(os.getenv("DEBUG")))

logging.config.dictConfig(logger_configuration)
logger = logging.getLogger("debug_logger" if DEBUG else "release_logger")

logger.info("hi", extra={"uh": 12})
