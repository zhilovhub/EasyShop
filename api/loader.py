import os

from dotenv import load_dotenv

from database.models.models import Database
from logs.config import db_logger

load_dotenv()
ALCHEMY_URL = os.getenv("SQLALCHEMY_URL")
DEBUG = bool(int(os.getenv("API_DEBUG_MODE")))
LOGS_PATH = os.getenv("PROJECT_ROOT") + "logs/"
MAIN_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
PROJECT_ROOT = os.getenv("PROJECT_ROOT")

db_engine = Database(ALCHEMY_URL, logger=db_logger)
