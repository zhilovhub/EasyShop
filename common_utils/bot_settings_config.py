from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

_bot_settings = {"parse_mode": ParseMode.HTML}

BOT_PROPERTIES = DefaultBotProperties(**_bot_settings)
