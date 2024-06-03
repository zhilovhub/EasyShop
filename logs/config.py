import logging
import logging.config
from dotenv import load_dotenv
import os

from logging import LogRecord


class LokiFilter(logging.Filter):

    def filter(self, record: LogRecord) -> bool:
        print(record.__dict__)
        return True


class ErrorWarningFilter(logging.Filter):

    def filter(self, record: LogRecord) -> bool:
        if record.levelno >= 30:
            return True

        return False


load_dotenv()

LOGS_PATH = os.getenv("PROJECT_ROOT") + "logs/"
# LOG_TO_GRAFANA = bool(int(os.getenv("LOG_TO_GRAFANA")))
LOG_TO_GRAFANA = 0

FORMATTER_NAME = "formatter"

logger_configuration = {
    "version": 1,
    "formatters": {
        FORMATTER_NAME: {
            "format": "{levelname} {asctime} {filename} {funcName}() {msg}",
            "style": "{"
        }
    },
    "filters": {
        "loki_filter": {
            "()": LokiFilter
        },
        "error_warning_filter": {
            "()": ErrorWarningFilter
        }
    },
    "handlers": {
        "console_handler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": FORMATTER_NAME,
        },
        "file_handler": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": FORMATTER_NAME,
            "filename": LOGS_PATH + "all.log"
        },
        "file_error_warning_handler": {
            "class": "logging.FileHandler",
            "level": "WARNING",
            "formatter": FORMATTER_NAME,
            "filename": LOGS_PATH + "err.log",
            "filters": ["error_warning_filter"]
        }
    },
    "loggers": {
        "local_logger": {
            "level": "DEBUG",
            "handlers": [
                "console_handler",
                "file_handler",
                "file_error_warning_handler"
            ]
        },
        "web_local_logger": {
            "level": "DEBUG",
            "handlers": [
                "console_handler",
                "file_handler",
                "file_error_warning_handler",
                "loki_handler"
            ]
        }
    }
}


def main():
    logger.info("hi", extra={"uh": 12})
    logger.info("hi1")
    logger.warning("hi2")
    logger.warning("hi2")
    logger.info("hi3")
    logger.error("hi4")


logging.config.dictConfig(logger_configuration)
logger = logging.getLogger("local_logger" if LOG_TO_GRAFANA else "web_local_logger")

main()
