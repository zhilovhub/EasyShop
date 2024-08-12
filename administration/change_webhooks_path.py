import asyncio

from aiogram import Bot

from common_utils.config import cryptography_settings
from common_utils.token_encryptor import TokenEncryptor
from common_utils.bot_settings_config import BOT_PROPERTIES

from database.models.models import Database
from database.models.bot_model import BotDao

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

        token_encryptor: TokenEncryptor = TokenEncryptor(cryptography_settings.TOKEN_SECRET_KEY)
        result = await bot.set_webhook(
            webhook_path.format(encrypted_bot_token=token_encryptor.encrypt_token(bot_token=bot.token)),
            allowed_updates=["message", "my_chat_member",
                             "callback_query", "chat_member", "channel_post",
                             "inline_query", "pre_checkout_query", "shipping_query"]
        )
        print(result, token)

if __name__ == '__main__':
    asyncio.run(main())
