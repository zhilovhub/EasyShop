import asyncio

from aiogram import Bot

from common_utils.bot_settings_config import BOT_PROPERTIES

from database.models.bot_model import BotDao
from database.models.models import Database

from logs.config import db_logger


database: Database = Database(
    sqlalchemy_url="",
    logger=db_logger
)
db_bot: BotDao = database.get_bot_dao()
webhook_path = ""


async def main() -> None:
    online_bot_tokens = list(map(lambda x: x.token, filter(lambda y: y.status == "online", await db_bot.get_bots())))
    for token in online_bot_tokens:
        bot = Bot(token=token, default=BOT_PROPERTIES)
        await bot.delete_webhook(drop_pending_updates=True)

        result = await bot.set_webhook(
            webhook_path.format(bot_token=token),
            allowed_updates=["message", "my_chat_member",
                             "callback_query", "chat_member", "channel_post"]
        )
        print(result, token)

if __name__ == '__main__':
    asyncio.run(main())
