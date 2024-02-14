import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from datetime import datetime
from database.models.models import Database

from bot import config
from bot.config import logger
from bot.utils.storage import AlchemyStorageAsync

bot = Bot(config.TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
storage = AlchemyStorageAsync(config.STORAGE_DB_URL, config.STORAGE_TABLE_NAME)
dp = Dispatcher(storage=storage)
db_engine = Database(config.DB_URL)


async def on_start():
    logger.info("Bot online.")
    await storage.connect()
    await db_engine.connect()
    await dp.start_polling(bot)


if __name__ == "__main__":
    from bot import handlers
    dp.include_router(handlers.router)

    for log_file in ('all.log', 'err.log'):
        with open(f'logs/{log_file}', 'a') as log:
            log.write(f'=============================\n'
                      f'New app session\n'
                      f'[{datetime.now()}]\n'
                      f'=============================\n')
    asyncio.run(on_start())
