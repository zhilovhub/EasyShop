import asyncio

from aiogram import Bot

from database.models.models import Database
from database.models.bot_model import BotDao
from database.models.order_model import OrderDao
from database.models.option_model import OptionDao, OptionSchemaWithoutId
from database.models.order_option_model import OrderOptionDao

from bot.utils import MessageTexts

from common_utils.bot_utils import create_order_options

from logs.config import db_logger


database: Database = Database(
    sqlalchemy_url="postgresql+asyncpg://postgres:wweof@92.118.114.106:7000/dev_ezshop",
    logger=db_logger,
    unique_id="test"
)
db_bot: BotDao = database.get_bot_dao()
db_order: OrderDao = database.get_order_dao()
db_options: OptionDao = database.get_option_dao()
db_order_option: OrderOptionDao = database.get_order_option_dao()


async def main() -> None:
    all_bots = await db_bot.get_bots()
    for bot in all_bots:
        bg_color = bot.settings.get("bg_color", None)
        start_msg = bot.settings.get("start_msg", MessageTexts.DEFAULT_START_MESSAGE.value)
        default_msg = bot.settings.get(
            "default_msg", f"Приветствую, этот бот создан с помощью @{(await Bot(token=bot.token).get_me()).username}"
        )
        auto_reduce = bot.settings.get("auto_reduce", True)
        web_app_button = bot.settings.get("web_app_button", MessageTexts.OPEN_WEB_APP_BUTTON_TEXT.value)
        post_order_msg = bot.settings.get("post_order_msg", None)

        options = OptionSchemaWithoutId(
            start_msg=start_msg,
            default_msg=default_msg,
            post_order_msg=post_order_msg,
            auto_reduce=auto_reduce,
            bg_color=bg_color,
            web_app_button=web_app_button
        )

        option_id = await db_options.add_option(options)
        bot.options_id = option_id
        await db_bot.update_bot(bot)

        await create_order_options(order_option_db=db_order_option, bot_id=bot.bot_id)
        print(bot, option_id)


if __name__ == '__main__':
    asyncio.run(main())
