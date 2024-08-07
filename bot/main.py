import asyncio

from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeChatAdministrators, BotCommandScopeAllPrivateChats
from aiogram.exceptions import TelegramBadRequest

from bot.stoke.stoke import Stoke

from common_utils.config import main_telegram_bot_settings, database_settings, common_settings
from common_utils.start_message import send_start_message_to_admins
from common_utils.storage.storage import AlchemyStorageAsync
from common_utils.scheduler.scheduler import Scheduler
from common_utils.bot_settings_config import BOT_PROPERTIES
from common_utils.cache_json.cache_json import JsonStore
from common_utils.subscription.subscription import Subscription

from database.config import db_engine

from logs.config import logger

bot = Bot(main_telegram_bot_settings.TELEGRAM_TOKEN, default=BOT_PROPERTIES)
storage = AlchemyStorageAsync(database_settings.SQLALCHEMY_URL, database_settings.STORAGE_TABLE_NAME)
dp = Dispatcher(storage=storage)

stock_manager = Stoke(db_engine)

_scheduler = Scheduler(database_settings.SCHEDULER_URL, 'postgres', database_settings.TIMEZONE)
subscription: Subscription = Subscription(database=db_engine, custom_scheduler=_scheduler)

cache_resources_file_id_store = JsonStore(
    file_path=common_settings.RESOURCES_PATH.format("cache.json"),
    json_store_name="RESOURCES_FILE_ID_STORE"
)
QUESTION_MESSAGES = JsonStore(
    file_path=common_settings.RESOURCES_PATH.format("question_messages.json"),
    json_store_name="QUESTION_MESSAGES"
)

MAINTENANCE = JsonStore(
    file_path=common_settings.RESOURCES_PATH.format("maintenance.json"),
    json_store_name="MAINTENANCE"
)

SENT_SUBSCRIPTION_NOTIFICATIONS = JsonStore(
    file_path=common_settings.RESOURCES_PATH.format("sent_sub_notifications.json"),
    json_store_name="SENT_SUB_NOTIFICATIONS"
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

    if main_telegram_bot_settings.BOT_DEBUG_MODE:
        commands.append(BotCommand(command="clear", description="Снести себя"))

    await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())

    try:
        await bot.set_my_commands(
            admin_commands,
            scope=BotCommandScopeChatAdministrators(chat_id=common_settings.ADMIN_GROUP_ID)
        )
    except TelegramBadRequest as e:
        logger.warning(
            f"Error while setting command to chat_id = {common_settings.ADMIN_GROUP_ID}",
            exc_info=e
        )

    await storage.connect()
    await db_engine.connect()

    await subscription.start_scheduler()

    logger.info("onStart finished. Bot online")

    await send_start_message_to_admins(bot=bot, admins=common_settings.TECH_ADMINS, msg_text="Main Bot started!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    from bot.handlers import (admin_bot_menu_router, channel_menu_router, custom_bot_editing_router, commands_router,
                              subscribe_router, stock_menu_router, post_message_router, admin_group_commands_router)

    dp.include_router(admin_group_commands_router)  # не знаю почему не работает если ставить не первым

    dp.include_router(commands_router)  # should be first
    dp.include_router(custom_bot_editing_router)  # should be before admin_bot_menu
    dp.include_router(admin_bot_menu_router)
    dp.include_router(stock_menu_router)
    dp.include_router(channel_menu_router)
    dp.include_router(subscribe_router)
    dp.include_router(post_message_router)

    for log_file in ('all.log', 'err.log'):
        with open(common_settings.LOGS_PATH + log_file, 'a') as log:
            log.write(f'=============================\n'
                      f'New bot-app session\n'
                      f'[{datetime.now()}]\n'
                      f'=============================\n')
    asyncio.run(on_start())
