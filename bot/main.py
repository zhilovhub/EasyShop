import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.client.bot import DefaultBotProperties
from channels_administration.competition.competition import CompetitionModule
from database.models.adv_model import AdvDao
from database.models.bot_model import BotDao
from database.models.channel_model import ChannelDao
from database.models.mailing_media_files import MailingMediaFileDao
from database.models.mailing_model import MailingDao
from database.models.models import Database
from database.models.user_model import UserDao
from database.models.order_model import OrderDao
from database.models.payment_model import PaymentDao
from database.models.product_model import ProductDao
from database.models.custom_bot_user_model import CustomBotUserDao
from database.models.channel_post_model import ChannelPostDao
from database.models.channel_post_media_files_model import ChannelPostMediaFileDao
from database.models.contest_channel_model import ContestChannelDao
from database.models.channel_user_model import ChannelUserDao
from database.models.contest_user_model import ContestUserDao
from subscription.subscription import Subscription
from subscription.scheduler import Scheduler
from bot import config
from bot.utils import AlchemyStorageAsync, JsonStore, send_start_message_to_admins
from stoke.stoke import Stoke

from logs.config import logger, db_logger

bot = Bot(config.TELEGRAM_TOKEN, default=DefaultBotProperties(
    parse_mode=ParseMode.HTML))
storage = AlchemyStorageAsync(config.SQLALCHEMY_URL, config.STORAGE_TABLE_NAME)
dp = Dispatcher(storage=storage)
db_engine: Database = Database(config.SQLALCHEMY_URL, db_logger)

bot_db: BotDao = db_engine.get_bot_dao()
adv_db: AdvDao = db_engine.get_adv_dao()
user_db: UserDao = db_engine.get_user_dao()
order_db: OrderDao = db_engine.get_order_dao()
pay_db: PaymentDao = db_engine.get_payment_dao()
product_db: ProductDao = db_engine.get_product_db()
channel_db: ChannelDao = db_engine.get_channel_dao()
mailing_db: MailingDao = db_engine.get_mailing_dao()
custom_bot_user_db: CustomBotUserDao = db_engine.get_custom_bot_user_db()
mailing_media_file_db: MailingMediaFileDao = db_engine.get_mailing_media_file_dao()
channel_post_db: ChannelPostDao = db_engine.get_channel_post_dao()
channel_post_media_file_db: ChannelPostMediaFileDao = db_engine.get_channel_post_media_file_dao()
channel_user_db: ChannelUserDao = db_engine.get_channel_user_dao()
contest_channel_db: ContestChannelDao = db_engine.get_contest_channel_dao()
contest_user_db: ContestUserDao = db_engine.get_contest_user_dao()

stock_manager = Stoke(db_engine)

_scheduler = Scheduler(config.SCHEDULER_URL, 'postgres', config.TIMEZONE)
subscription = Subscription(database=db_engine, scheduler=_scheduler)

competition: CompetitionModule = CompetitionModule(db_engine)

cache_resources_file_id_store = JsonStore(
    file_path=config.RESOURCES_PATH.format("cache.json"),
    json_store_name="RESOURCES_FILE_ID_STORE"
)
QUESTION_MESSAGES = JsonStore(
    file_path=config.RESOURCES_PATH.format("question_messages.json"),
    json_store_name="QUESTION_MESSAGES"
)


async def on_start():
    logger.info("onStart called")

    commands = [
        BotCommand(command="start", description="Стартовая инструкция"),
        BotCommand(command="check_subscription",
                   description="Проверить подписку"),
    ]

    if config.BOT_DEBUG_MODE:
        commands.append(BotCommand(command="clear", description="Снести себя"))

    await bot.set_my_commands(commands)

    await storage.connect()
    await db_engine.connect()

    await subscription.start_scheduler()

    logger.info("onStart finished. Bot online")

    await send_start_message_to_admins(bot=bot, admins=config.ADMINS, msg_text="Main Bot started!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    from bot.handlers import (admin_bot_menu_router, channel_menu_router, custom_bot_editing_router, commands_router,
                              subscribe_router, stock_menu_router)
    dp.include_router(commands_router)  # should be first
    dp.include_router(admin_bot_menu_router)
    dp.include_router(channel_menu_router)
    dp.include_router(subscribe_router)
    dp.include_router(custom_bot_editing_router)
    dp.include_router(stock_menu_router)

    for log_file in ('all.log', 'err.log'):
        with open(config.LOGS_PATH + log_file, 'a') as log:
            log.write(f'=============================\n'
                      f'New bot-app session\n'
                      f'[{datetime.now()}]\n'
                      f'=============================\n')
    asyncio.run(on_start())
