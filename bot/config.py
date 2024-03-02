import os
import logging.config
from dotenv import load_dotenv

# Загрузка .env файла
load_dotenv()

# Resources path
RESOURCES_PATH = os.getenv("PROJECT_ROOT") + "resources/{}"

# Telegram bot variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SQLALCHEMY_URL = os.getenv("SQLALCHEMY_URL")

# WebApp variables
WEB_APP_URL = os.getenv("WEB_APP_URL")
WEB_APP_PORT = os.getenv("WEB_APP_PORT")

# Local MultiBots Api
LOCAL_API_SERVER_HOST = os.getenv("WEBHOOK_LOCAL_API_URL")
LOCAL_API_SERVER_PORT = int(os.getenv("WEBHOOK_LOCAL_API_PORT"))

# Telegram bot FSM storage variables
STORAGE_TABLE_NAME = os.getenv("STORAGE_TABLE_NAME")

# Other
DEBUG = bool(int(os.getenv("DEBUG")))

# Logging
LOGGING_SETUP = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'log_formatter': {
            'format': '[{asctime}][{levelname}] ::: {filename}({lineno}) -> {message}',
            'style': '{',
        },
    },
    'handlers': {
        'all_file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/all.log',  # путь до файла логирования
            'formatter': 'log_formatter',
        },
        'error_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/err.log',  # путь до файла логирования ошибок
            'formatter': 'log_formatter',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'log_formatter',
        },
    },
    'loggers': {
        'logger': {
            'handlers': ['all_file', 'error_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}
logging.config.dictConfig(LOGGING_SETUP)
logging.basicConfig(format=u'[%(asctime)s][%(levelname)s] ::: %(filename)s(%(lineno)d) -> %(message)s',
                    level="INFO", filename='logs/all.log')
logger = logging.getLogger('logger')