import os

from dotenv import load_dotenv

from database.models.models import Database

load_dotenv()
ALCHEMY_URL = os.getenv("SQLALCHEMY_URL")
DEBUG = bool(int(os.getenv("DEBUG")))

db_engine = Database(ALCHEMY_URL)
