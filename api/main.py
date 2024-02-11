import os
from fastapi import FastAPI
from database.models.models import Database
from dotenv import load_dotenv
import datetime
import logging
import logging.config

tags_metadata = [
    {
        "name": "products",
        "description": "Operations with products.",
    },
    {
        "name": "orders",
        "description": "Operations with orders.",
    },
]
app = FastAPI(openapi_tags=tags_metadata)
ROOT_PATH = "/api/"

load_dotenv()
ALCHEMY_URL = os.getenv("SQLALCHEMY_URL")
DEBUG = bool(os.getenv("DEBUG"))

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
            'filename': 'api/logs/all.log',  # путь до файла логирования
            'formatter': 'log_formatter',
        },
        'error_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'api/logs/err.log',  # путь до файла логирования ошибок
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
                    level="INFO", filename='api/logs/all.log')
logger = logging.getLogger('logger')


@app.get(f"{ROOT_PATH}")
async def read_root():
    return "You can see all available methods in rest api docs"


for log_file in ('all.log', 'err.log'):
    with open(f'api/logs/{log_file}', 'a') as log:
        log.write(f'=============================\n'
                  f'New app session\n'
                  f'[{datetime.datetime.now()}]\n'
                  f'=============================\n')

if __name__ == "api.main":
    import api.products
    import api.orders
