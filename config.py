from dotenv import load_dotenv
from os import environ

load_dotenv()

SQLALCHEMY_URL = environ.get("SQLALCHEMY_URL")
