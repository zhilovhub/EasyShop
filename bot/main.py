import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from database.models.models import Database

from subscription.subscription import Subscription
from subscription.scheduler import Scheduler

from bot import config
from bot.config import logger
from bot.utils import AlchemyStorageAsync

bot = Bot(config.TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
storage = AlchemyStorageAsync(config.SQLALCHEMY_URL, config.STORAGE_TABLE_NAME)
dp = Dispatcher(storage=storage)
db_engine: Database = Database(config.SQLALCHEMY_URL)

_scheduler = Scheduler(config.SCHEDULER_URL, 'postgres', config.TIMEZONE)
subscription = Subscription(database=db_engine, scheduler=_scheduler)


async def on_start():
    logger.info("onStart called")

    commands = [
        BotCommand(command="start", description="Стартовая инструкция"),
        BotCommand(command="check_subscription", description="Проверить подписку"),
    ]

    if config.BOT_DEBUG_MODE:
        commands.append(BotCommand(command="clear", description="Снести себя"))

    await bot.set_my_commands(commands)

    await storage.connect()
    await db_engine.connect()

    await subscription.start_scheduler()

    logger.info("onStart finished. Bot online")
    await dp.start_polling(bot)


if __name__ == "__main__":
    from bot import handlers

    dp.include_router(handlers.all_router)
    dp.include_router(handlers.router)

    for log_file in ('all.log', 'err.log'):
        with open(config.LOGS_PATH + log_file, 'a') as log:
            log.write(f'=============================\n'
                      f'New app session\n'
                      f'[{datetime.now()}]\n'
                      f'=============================\n')
    asyncio.run(on_start())
