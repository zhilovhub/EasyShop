import logging  # noqa
import logging.config
import logging_loki  # noqa

from re import compile, sub, UNICODE
import os

from logging import LogRecord

from common_utils.env_config import LOGS_PATH, FROM, LOG_TO_GRAFANA, GRAFANA_URL

from typing import TypedDict, Unpack

try:
    os.mkdir(LOGS_PATH)
except FileExistsError:
    pass

if not FROM:
    raise Exception("В .env присвойте переменной FROM Ваше имя, чтобы в логах можно было фильтроваться")

GRAFANA_FORMATTER_NAME = "formatter_grafana"
LOCAL_FORMATTER_NAME = "formatter_local"


class RequestParams(TypedDict, total=False):
    bot_id: int
    user_id: int
    product_review_id: int
    category_id: int
    channel_id: int
    channel_user_id: int
    channel_post_id: int
    post_message_id: int
    order_id: int
    product_id: int
    payment_id: int
    adv_id: int
    job_id: str
    contest_id: int
    partnership_id: int
    bot_token: str


def extra_params(**kwargs: Unpack[RequestParams]):
    return {
        "tags": kwargs
    }


class EmotionsFilter(logging.Filter):

    def filter(self, record: LogRecord) -> bool:
        emotions = compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002500-\U00002BEF"  # chinese char
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           u"\U0001f926-\U0001f937"
                           u"\U00010000-\U0010ffff"
                           u"\u2640-\u2642"
                           u"\u2600-\u2B55"
                           u"\u200d"
                           u"\u23cf"
                           u"\u23e9"
                           u"\u231a"
                           u"\ufe0f"  # dingbats
                           u"\u3030"
                           "]+", UNICODE)
        record.msg = sub(emotions, '*', record.msg)

        return True


class LokiFilter(logging.Filter):

    def filter(self, record: LogRecord) -> bool:
        if hasattr(record, "tags"):
            if hasattr(record, "product_review_id"):
                record.tags["product_review_id"] = record.product_review_id
            if hasattr(record, "user_id"):
                record.tags["user_id"] = record.user_id
            if hasattr(record, "bot_id"):
                record.tags["bot_id"] = record.bot_id
            if hasattr(record, "category_id"):
                record.tags["category_id"] = record.category_id
            if hasattr(record, "channel_id"):
                record.tags["channel_id"] = record.channel_id
            if hasattr(record, "channel_user_id"):
                record.tags["channel_user_id"] = record.channel_user_id
            if hasattr(record, "channel_post_id"):
                record.tags["channel_post_id"] = record.channel_post_id
            if hasattr(record, "post_message_id"):
                record.tags["post_message_id"] = record.post_message_id
            if hasattr(record, "order_id"):
                record.tags["order_id"] = record.order_id
            if hasattr(record, "product_id"):
                record.tags["product_id"] = record.product_id
            if hasattr(record, "payment_id"):
                record.tags["payment_id"] = record.payment_id
            if hasattr(record, "adv_id"):
                record.tags["adv_id"] = record.adv_id
            if hasattr(record, "job_id"):
                record.tags["job_id"] = record.job_id
            if hasattr(record, "contest_id"):
                record.tags["contest_id"] = record.contest_id
            if hasattr(record, "partnership_id"):
                record.tags["partnership_id"] = record.partnership_id
            if hasattr(record, "bot_token"):
                # hide the token from gr
                record.msg = record.msg.replace(record.bot_token[5:-1], "*" * len(record.bot_token[5:-1]))
            if "bot_token" in record.tags:
                # hide the token from gr
                record.msg = record.msg.replace(
                    record.tags["bot_token"][5:-1],
                    "*" * len(record.tags["bot_token"][5:-1])
                )

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
            "format": "{levelname} {asctime} {filename} {funcName}() {msg}",
            "style": "{"
        },
        GRAFANA_FORMATTER_NAME: {
            "format": "{filename} {funcName}() {msg}",
            "style": "{"
        }
    },
    "filters": {
        "emotions_filter": {
            "()": EmotionsFilter
        },
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
            "filters": ["emotions_filter"]
        },
        "file_handler": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": LOCAL_FORMATTER_NAME,
            "filename": LOGS_PATH + "all.log",
            "filters": ["emotions_filter"]
        },
        "file_error_warning_handler": {
            "class": "logging.FileHandler",
            "level": "WARNING",
            "formatter": LOCAL_FORMATTER_NAME,
            "filename": LOGS_PATH + "err.log",
            "filters": ["error_warning_filter", "emotions_filter"]
        },
        "loki_handler": {
            "class": "logging_loki.LokiHandler",
            "level": "DEBUG",
            "formatter": GRAFANA_FORMATTER_NAME,
            "url": GRAFANA_URL + "loki/api/v1/push",
            "tags": {"from": FROM},
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
                "loki_handler"
            ]
        },
        "api_logger": {
            "level": "DEBUG",
            "handlers": [
                "console_handler",
                "file_handler",
                "file_error_warning_handler",
                "loki_handler"
            ]
        },
        "custom_bot_logger": {
            "level": "DEBUG",
            "handlers": [
                "console_handler",
                "file_handler",
                "file_error_warning_handler",
                "loki_handler"
            ]
        },
        "adv_logger": {
            "level": "INFO",
            "handlers": [
                "console_handler",
                "file_handler",
                "file_error_warning_handler",
                "loki_handler"
            ]
        }
    }
}

logging.config.dictConfig(logger_configuration)
logger = logging.getLogger("general_logger")
db_logger = logging.getLogger("db_logger")
api_logger = logging.getLogger("api_logger")
custom_bot_logger = logging.getLogger("custom_bot_logger")
adv_logger = logging.getLogger("adv_logger")
