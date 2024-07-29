import asyncio

from aiogram import Bot

from common_utils.bot_settings_config import BOT_PROPERTIES

from database.models.bot_model import BotDao
from database.models.models import Database

from logs.config import db_logger


database: Database = Database(
    sqlalchemy_url="postgresql+asyncpg://database_module:UuHgSEzf_75QC!Nn@92.118.114.106/easybots_db",
    logger=db_logger
)
db_bot: BotDao = database.get_bot_dao()


async def main() -> None:
    online_bot_tokens = list(map(lambda x: x.token, filter(lambda y: y.status == "online", await db_bot.get_bots())))
    for token in online_bot_tokens:
        bot = Bot(token=token, default=BOT_PROPERTIES)


if __name__ == '__main__':
    asyncio.run(main())
