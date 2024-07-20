import os
from dotenv import load_dotenv


class EmptyEnvVariable(Exception):
    def __init__(self, message):
        super().__init__(message)


def _get_env(var_name: str, raise_if_none: bool = True) -> str | None:
    variable = os.getenv(var_name)
    if variable is None and raise_if_none:
        raise EmptyEnvVariable(var_name)

    return variable


# load_dotenv()  # TODO back after docker compose
load_dotenv("/common_utils/.env")

# COMMON
PROJECT_ROOT = _get_env("PROJECT_ROOT")
FILES_PATH = _get_env("FILES_PATH")
RESOURCES_PATH = _get_env("PROJECT_ROOT") + "resources/{}"
TELEGRAM_TOKEN = _get_env("TELEGRAM_TOKEN")
TIMEZONE = _get_env("TIMEZONE")

SCHEDULER_URL = _get_env("SCHEDULER_URL")

ADMINS = [int(uid.strip()) for uid in _get_env("ADMINS").split(',')]
TECH_ADMINS = [int(uid.strip()) for uid in _get_env("TECH_ADMINS").split(',')]
ADMIN_GROUP_ID = _get_env("ADMIN_GROUP_ID")

LOGS_PATH = _get_env("PROJECT_ROOT") + "logs/"

# API env
API_PROTOCOL = _get_env("API_PROTOCOL")
API_HOST = _get_env("API_HOST")
API_PORT = int(_get_env("API_PORT"))

SSL_KEY_PATH = _get_env("SSL_KEY_PATH", raise_if_none=False)
SSL_CERT_PATH = _get_env("SSL_CERT_PATH", raise_if_none=False)

API_DEBUG_MODE = bool(int(_get_env("API_DEBUG_MODE")))

# DATABASE env
SQLALCHEMY_URL = _get_env("SQLALCHEMY_URL")

# Main Telegram Bot env
BOT_DEBUG_MODE = bool(int(_get_env("BOT_DEBUG_MODE")))
STORAGE_TABLE_NAME = _get_env("STORAGE_TABLE_NAME")

DESTINATION_PHONE_NUMBER = _get_env("DESTINATION_PHONE_NUMBER")
SBP_URL = _get_env("SBP_PAYMENT_URL")

# Custom Telegram Bot env
CUSTOM_BOT_STORAGE_DB_URL = _get_env("CUSTOM_BOT_STORAGE_DB_URL")
CUSTOM_BOT_STORAGE_TABLE_NAME = _get_env("CUSTOM_BOT_STORAGE_TABLE_NAME")

WEBHOOK_URL = _get_env("WEBHOOK_URL")
WEBHOOK_HOST = _get_env("WEBHOOK_HOST")
WEBHOOK_PORT = int(_get_env("WEBHOOK_PORT"))

WEB_APP_URL = _get_env("WEB_APP_URL")
WEB_APP_PORT = _get_env("WEB_APP_PORT")

LOCAL_API_SERVER_HOST =_get_env("WEBHOOK_LOCAL_API_URL_HOST")
LOCAL_API_SERVER_OUTSIDE =_get_env("WEBHOOK_LOCAL_API_URL_OUTSIDE")
LOCAL_API_SERVER_PORT = int(_get_env("WEBHOOK_LOCAL_API_PORT"))

try:
    WEBHOOK_SERVER_PORT_TO_REDIRECT = int(_get_env("WEBHOOK_SERVER_PORT_TO_REDIRECT"))
except EmptyEnvVariable as e:
    WEBHOOK_SERVER_PORT_TO_REDIRECT = WEBHOOK_PORT

# LOGS
LOG_TO_GRAFANA = bool(int(_get_env("LOG_TO_GRAFANA")))
GRAFANA_URL = _get_env("GRAFANA_URL")
FROM = _get_env("FROM")

# TESTS
SCHEDULER_FOR_TESTS = _get_env("SCHEDULER_FOR_TESTS", raise_if_none=False)
DB_FOR_TESTS = _get_env("DB_FOR_TESTS", raise_if_none=False)
