import logging.config
import os

from dotenv import load_dotenv

from database.models.models import Database

load_dotenv()
ALCHEMY_URL = os.getenv("SQLALCHEMY_URL")
DEBUG = bool(int(os.getenv("DEBUG")))

db_engine = Database(ALCHEMY_URL)

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
