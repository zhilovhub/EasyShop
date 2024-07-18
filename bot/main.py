import asyncio

from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeChatAdministrators, BotCommandScopeAllPrivateChats
from aiogram.exceptions import TelegramBadRequest

from bot.stoke.stoke import Stoke
from common_utils.subscription.subscription import Subscription
from common_utils.bot_settings_config import BOT_PROPERTIES

from common_utils.env_config import SQLALCHEMY_URL, TIMEZONE, SCHEDULER_URL, TELEGRAM_TOKEN, STORAGE_TABLE_NAME, \
    RESOURCES_PATH, BOT_DEBUG_MODE, TECH_ADMINS, LOGS_PATH, ADMIN_GROUP_ID
from common_utils.start_message import send_start_message_to_admins
from common_utils.storage.storage import AlchemyStorageAsync
from common_utils.scheduler.scheduler import Scheduler
from common_utils.cache_json.cache_json import JsonStore

from database.config import db_engine

from logs.config import logger

bot = Bot(TELEGRAM_TOKEN, default=BOT_PROPERTIES)
storage = AlchemyStorageAsync(SQLALCHEMY_URL, STORAGE_TABLE_NAME)
dp = Dispatcher(storage=storage)

stock_manager = Stoke(db_engine)

_scheduler = Scheduler(SCHEDULER_URL, 'postgres', TIMEZONE)
subscription = Subscription(database=db_engine, custom_scheduler=_scheduler)

cache_resources_file_id_store = JsonStore(
    file_path=RESOURCES_PATH.format("cache.json"),
    json_store_name="RESOURCES_FILE_ID_STORE"
)
QUESTION_MESSAGES = JsonStore(
    file_path=RESOURCES_PATH.format("question_messages.json"),
    json_store_name="QUESTION_MESSAGES"
)

MAINTENANCE = JsonStore(
    file_path=RESOURCES_PATH.format("maintenance.json"),
    json_store_name="MAINTENANCE"
)


async def on_start():
    logger.info("onStart called")

    commands = [
        BotCommand(command="start", description="Стартовая инструкция"),
        BotCommand(command="check_subscription",
                   description="Проверить подписку"),
    ]
    admin_commands = [
        BotCommand(command="bot_status", description="Статус бота"),
        BotCommand(command="on_maintenance", description="Включить тех обсл"),
        BotCommand(command="off_maintenance", description="Выключить тех обсл"),
    ]

    if BOT_DEBUG_MODE:
        commands.append(BotCommand(command="clear", description="Снести себя"))

    await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())

    try:
        await bot.set_my_commands(
            admin_commands,
            scope=BotCommandScopeChatAdministrators(chat_id=ADMIN_GROUP_ID)
        )
    except TelegramBadRequest as e:
        logger.warning(
            f"Error while setting command to chat_id = {ADMIN_GROUP_ID}",
            exc_info=e
        )

    await storage.connect()
    await db_engine.connect()

    await subscription.start_scheduler()

    logger.info("onStart finished. Bot online")

    await send_start_message_to_admins(bot=bot, admins=TECH_ADMINS, msg_text="Main Bot started!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    from bot.handlers import (admin_bot_menu_router, channel_menu_router, custom_bot_editing_router, commands_router,
                              subscribe_router, stock_menu_router, post_message_router, admin_group_commands_router,
                              empty_router)

    dp.include_router(admin_group_commands_router)  # не знаю почему не работает если ставить не первым

    dp.include_router(commands_router)  # should be first
    dp.include_router(admin_bot_menu_router)
    dp.include_router(stock_menu_router)
    dp.include_router(channel_menu_router)
    dp.include_router(subscribe_router)
    dp.include_router(custom_bot_editing_router)
    dp.include_router(post_message_router)
    dp.include_router(empty_router)  # should be last

    for log_file in ('all.log', 'err.log'):
        with open(LOGS_PATH + log_file, 'a') as log:
            log.write(f'=============================\n'
                      f'New bot-app session\n'
                      f'[{datetime.now()}]\n'
                      f'=============================\n')
    asyncio.run(on_start())
