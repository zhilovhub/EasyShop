from pathlib import Path
from aiogram import Bot, Dispatcher, types
from bot import config
from bot.utils.database import AlchemyDB
from bot.utils.storage import AlchemyStorageAsync
from aiogram.enums import ParseMode
import asyncio
from bot.config import logger
import datetime
from bot.utils.database import DbUser

# app_dir: Path = Path(__file__).parent.parent
# locales_dir = app_dir / "locales"

bot = Bot(config.TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
storage = AlchemyStorageAsync(config.STORAGE_DB_URL, config.STORAGE_TABLE_NAME)
dp = Dispatcher(storage=storage)
db = AlchemyDB(config.DB_URL)


async def on_start():
    logger.info("Bot online.")
    await storage.connect()
    await db.connect()
    await dp.start_polling(bot)


if __name__ == "__main__":
    from bot import handlers, filters, keyboards

    dp.include_router(handlers.users.router)
    dp.include_router(keyboards.user_kb_handlers.router)

    for log_file in ('all.log', 'err.log'):
        with open(f'logs/{log_file}', 'a') as log:
            log.write(f'=============================\n'
                      f'New app session\n'
                      f'[{datetime.datetime.now()}]\n'
                      f'=============================\n')
    asyncio.run(on_start())
