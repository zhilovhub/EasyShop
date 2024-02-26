from aiogram.types import WebAppInfo
from bot.config import WEB_APP_URL, WEB_APP_PORT


def make_webapp_info(bot_id: int) -> WebAppInfo:
    return WebAppInfo(url=f"{WEB_APP_URL}:{WEB_APP_PORT}?bot_id={bot_id}")
