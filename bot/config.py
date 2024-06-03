import os
from dotenv import load_dotenv

# Загрузка .env файла
load_dotenv()

# Resources path
RESOURCES_PATH = os.getenv("PROJECT_ROOT") + "resources/{}"

# Telegram bot variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMINS = [int(uid.strip()) for uid in os.getenv("ADMINS").split(',')]
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID")

# Database variables
SQLALCHEMY_URL = os.getenv("SQLALCHEMY_URL")
SCHEDULER_URL = os.getenv("SCHEDULER_URL")

# WebApp variables
WEB_APP_URL = os.getenv("WEB_APP_URL")
WEB_APP_PORT = os.getenv("WEB_APP_PORT")

# Local MultiBots Api
LOCAL_API_SERVER_HOST = os.getenv("WEBHOOK_LOCAL_API_URL")
LOCAL_API_SERVER_PORT = int(os.getenv("WEBHOOK_LOCAL_API_PORT"))

# Telegram bot FSM storage variables
STORAGE_TABLE_NAME = os.getenv("STORAGE_TABLE_NAME")

# Pay variables
SBP_URL = os.getenv("SBP_PAYMENT_URL")

# Other
DEBUG = bool(int(os.getenv("DEBUG")))
TIMEZONE = os.getenv("TIMEZONE")

BOT_DEBUG_MODE = bool(int(os.getenv("BOT_DEBUG_MODE")))

LOGS_PATH = os.getenv("PROJECT_ROOT") + "logs/"
