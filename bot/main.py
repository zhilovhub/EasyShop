import os

from aiogram import Bot, Dispatcher, types
from bot import config
from bot.utils.database import AlchemyDB
from bot.utils.storage import AlchemyStorageAsync
from aiogram.enums import ParseMode
import asyncio
from bot.config import logger
import datetime
from database.models.models import Database
from database.models.order_model import OrderDao


bot = Bot(config.TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
storage = AlchemyStorageAsync(config.STORAGE_DB_URL, config.STORAGE_TABLE_NAME)
dp = Dispatcher(storage=storage)
db = AlchemyDB(config.DB_URL)
db_engine = Database(config.DB_URL)
products_db = db_engine.get_product_db()


async def on_start():
    logger.info("Bot online.")
    await storage.connect()
    await db.connect()
    await dp.start_polling(bot)


if __name__ == "__main__":
    from bot import handlers, filters, keyboards, states
    dp.include_router(handlers.users.router)
    dp.include_router(keyboards.user_kb_handlers.router)
    dp.include_router(states.user_states_handler.router)

    for log_file in ('all.log', 'err.log'):
        with open(f'logs/{log_file}', 'a') as log:
            log.write(f'=============================\n'
                      f'New app session\n'
                      f'[{datetime.datetime.now()}]\n'
                      f'=============================\n')
    asyncio.run(on_start())
