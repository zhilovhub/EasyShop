import logging  # noqa
import logging.config
import logging_loki  # noqa

from re import compile, sub, UNICODE
import os

from logging import LogRecord

from common_utils.config import logs_settings, common_settings

try:
    os.mkdir(common_settings.LOGS_PATH)
except Exception:  # noqa
    pass

if not logs_settings.FROM:
    raise Exception("В .env присвойте переменной FROM Ваше имя, чтобы в логах можно было фильтроваться")

GRAFANA_FORMATTER_NAME = "formatter_grafana"
LOCAL_FORMATTER_NAME = "formatter_local"


def extra_params(**kwargs):
    return {"tags": kwargs}


class EmotionsFilter(logging.Filter):
    def filter(self, record: LogRecord) -> bool:
        emotions = compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "\U00002500-\U00002bef"  # chinese char
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2b55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"  # dingbats
            "\u3030"
            "]+",
            UNICODE,
        )
        record.msg = sub(emotions, "*", record.msg)

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
            if hasattr(record, "criteria_id"):
                record.tags["criteria_id"] = record.criteria_id
            if hasattr(record, "order_option_id"):
                record.tags["order_option_id"] = record.order_option_id
            if hasattr(record, "bot_token"):
                # hide the token from gr
                record.msg = record.msg.replace(record.bot_token[5:-1], "*" * len(record.bot_token[5:-1]))
            if hasattr(record, "invite_id"):
                record.tags["invite_id"] = record.invite_id
            if "bot_token" in record.tags:
                # hide the token from gr
                record.msg = record.msg.replace(
                    record.tags["bot_token"][5:-1], "*" * len(record.tags["bot_token"][5:-1])
                )

        return logs_settings.LOG_TO_GRAFANA


class ErrorWarningFilter(logging.Filter):
    def filter(self, record: LogRecord) -> bool:
        if record.levelno >= 30:
            return True

        return False


logger_configuration = {
    "version": 1,
    "formatters": {
        LOCAL_FORMATTER_NAME: {"format": "{levelname} {asctime} {filename} {funcName}() {msg}", "style": "{"},
        GRAFANA_FORMATTER_NAME: {"format": "{filename} {funcName}() {msg}", "style": "{"},
    },
    "filters": {
        "emotions_filter": {"()": EmotionsFilter},
        "loki_filter": {"()": LokiFilter},
        "error_warning_filter": {"()": ErrorWarningFilter},
    },
    "handlers": {
        "console_handler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": LOCAL_FORMATTER_NAME,
            "filters": ["emotions_filter"],
        },
        "file_handler": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": LOCAL_FORMATTER_NAME,
            "filename": common_settings.LOGS_PATH + "all.log",
            "filters": ["emotions_filter"],
        },
        "file_error_warning_handler": {
            "class": "logging.FileHandler",
            "level": "WARNING",
            "formatter": LOCAL_FORMATTER_NAME,
            "filename": common_settings.LOGS_PATH + "err.log",
            "filters": ["error_warning_filter", "emotions_filter"],
        },
        "loki_handler": {
            "class": "logging_loki.LokiHandler",
            "level": "DEBUG",
            "formatter": GRAFANA_FORMATTER_NAME,
            "url": logs_settings.GRAFANA_URL + "loki/api/v1/push",
            "tags": {"from": logs_settings.FROM},
            "filters": ["loki_filter"],
            "version": "1",
        },
    },
    "loggers": {
        "general_logger": {
            "level": "DEBUG",
            "handlers": ["console_handler", "file_handler", "file_error_warning_handler", "loki_handler"],
        },
        "db_logger": {
            "level": "DEBUG",
            "handlers": ["console_handler", "file_handler", "file_error_warning_handler", "loki_handler"],
        },
        "api_logger": {
            "level": "DEBUG",
            "handlers": ["console_handler", "file_handler", "file_error_warning_handler", "loki_handler"],
        },
        "custom_bot_logger": {
            "level": "DEBUG",
            "handlers": ["console_handler", "file_handler", "file_error_warning_handler", "loki_handler"],
        },
        "tech_support_logger": {
            "level": "DEBUG",
            "handlers": ["console_handler", "file_handler", "file_error_warning_handler", "loki_handler"],
        },
        "test_logger": {"level": "DEBUG", "handlers": ["console_handler"]},
    },
}

logging.config.dictConfig(logger_configuration)
logger = logging.getLogger("general_logger")
db_logger = logging.getLogger("db_logger")
api_logger = logging.getLogger("api_logger")
custom_bot_logger = logging.getLogger("custom_bot_logger")
tech_support_logger = logging.getLogger("tech_support_logger")

test_logger = logging.getLogger("test_logger")
