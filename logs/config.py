import logging
import logging.config
import logging_loki

from dotenv import load_dotenv
import os

from logging import LogRecord

load_dotenv()

LOG_TO_GRAFANA = bool(int(os.getenv("LOG_TO_GRAFANA")))

LOGS_PATH = os.getenv("PROJECT_ROOT") + "logs/"
GRAFANA_URL = os.getenv("GRAFANA_URL")

GRAFANA_FORMATTER_NAME = "formatter_grafana"
LOCAL_FORMATTER_NAME = "formatter_local"


def extra_params(**kwargs):
    return {
        "tags": kwargs
    }


class LokiFilter(logging.Filter):

    def filter(self, record: LogRecord) -> bool:
        print(record.__dict__)
        if hasattr(record, "tags"):
            if hasattr(record, "user_id"):
                record.tags["user_id"] = record.user_id
            if hasattr(record, "bot_id"):
                record.tags["bot_id"] = record.bot_id
            if hasattr(record, "category_id"):
                record.tags["category_id"] = record.category_id
            if hasattr(record, "channel_id"):
                record.tags["channel_id"] = record.channel_id
            if hasattr(record, "competition_id"):
                record.tags["competition_id"] = record.competition_id
            if hasattr(record, "mailing_id"):
                record.tags["mailing_id"] = record.mailing_id
            if hasattr(record, "order_id"):
                record.tags["order_id"] = record.order_id
            if hasattr(record, "payment_id"):
                record.tags["payment_id"] = record.payment_id
            if hasattr(record, "bot_token"):
                record.msg.replace(record.bot_token[5:-1], "*" * len(record.bot_token[5:-1]))  # hide the token from gr

        return LOG_TO_GRAFANA


class ErrorWarningFilter(logging.Filter):

    def filter(self, record: LogRecord) -> bool:
        if record.levelno >= 30:
            return True

        return False


logger_configuration = {
    "version": 1,
    "formatters": {
        LOCAL_FORMATTER_NAME: {
            "format": "{levelname} {asctime} {filename} {funcName}()/{lineno} {msg}",
            "style": "{"
        },
        GRAFANA_FORMATTER_NAME: {
            "format": "{filename} {funcName}()/{lineno} {msg}",
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
            "formatter": LOCAL_FORMATTER_NAME,
        },
        "file_handler": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": LOCAL_FORMATTER_NAME,
            "filename": LOGS_PATH + "all.log"
        },
        "file_error_warning_handler": {
            "class": "logging.FileHandler",
            "level": "WARNING",
            "formatter": LOCAL_FORMATTER_NAME,
            "filename": LOGS_PATH + "err.log",
            "filters": ["error_warning_filter"]
        },
        "loki_handler": {
            "class": "logging_loki.LokiHandler",
            "level": "DEBUG",
            "formatter": GRAFANA_FORMATTER_NAME,
            "url": GRAFANA_URL + "loki/api/v1/push",
            "tags": {"type": "general"},
            "filters": ["loki_filter"],
            "version": "1"
        },
        "loki_db_handler": {
            "class": "logging_loki.LokiHandler",
            "level": "DEBUG",
            "formatter": GRAFANA_FORMATTER_NAME,
            "url": GRAFANA_URL + "loki/api/v1/push",
            "tags": {"type": "db"},
            "filters": ["loki_filter"],
            "version": "1"
        },
        "loki_api_handler": {
            "class": "logging_loki.LokiHandler",
            "level": "DEBUG",
            "formatter": GRAFANA_FORMATTER_NAME,
            "url": GRAFANA_URL + "loki/api/v1/push",
            "tags": {"type": "api"},
            "filters": ["loki_filter"],
            "version": "1"
        },
        "loki_custom_bot_handler": {
            "class": "logging_loki.LokiHandler",
            "level": "DEBUG",
            "formatter": GRAFANA_FORMATTER_NAME,
            "url": GRAFANA_URL + "loki/api/v1/push",
            "tags": {"type": "custom_bot"},
            "filters": ["loki_filter"],
            "version": "1"
        },
    },
    "loggers": {
        "general_logger": {
            "level": "DEBUG",
            "handlers": [
                "console_handler",
                "file_handler",
                "file_error_warning_handler",
                "loki_handler"
            ]
        },
        "db_logger": {
            "level": "DEBUG",
            "handlers": [
                "console_handler",
                "file_handler",
                "file_error_warning_handler",
                "loki_db_handler"
            ]
        },
        "api_logger": {
            "level": "DEBUG",
            "handlers": [
                "console_handler",
                "file_handler",
                "file_error_warning_handler",
                "loki_api_handler"
            ]
        },
        "custom_bot_logger": {
            "level": "DEBUG",
            "handlers": [
                "console_handler",
                "file_handler",
                "file_error_warning_handler",
                "loki_custom_bot_handler"
            ]
        }
    }
}

logging.config.dictConfig(logger_configuration)
logger = logging.getLogger("general_logger")
db_logger = logging.getLogger("db_logger")
api_logger = logging.getLogger("api_logger")
custom_bot_logger = logging.getLogger("custom_bot_logger")
