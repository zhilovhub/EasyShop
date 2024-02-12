import os
import asyncio
import datetime
import logging
import dotenv

from re import fullmatch

from sqlalchemy import MetaData
from sqlalchemy import Table, Column, String, JSON, BigInteger, DateTime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, Chat, User
from aiogram.filters import CommandStart, StateFilter
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.web_app_info import WebAppInfo

dotenv.load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
DB_URL = os.getenv("DB_URL")
WEB_APP_URL = os.getenv("WEB_APP_URL")

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
# storage = AlchemyStorageAsync(config.STORAGE_DB_URL, config.STORAGE_TABLE_NAME)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
# db = AlchemyDB(DB_URL)
logging.basicConfig(format=u'[%(asctime)s][%(levelname)s] ::: %(filename)s(%(lineno)d) -> %(message)s',
                    level="INFO", filename='logs/all.log')

metadata = MetaData()
bots = Table('bots', metadata,
             Column('bot_token', String(46), primary_key=True),
             Column('status', String(55), nullable=False),
             Column('created_at', DateTime, nullable=False),
             Column('created_by', BigInteger, nullable=False),
             Column('settings', JSON),
             Column('locale', String(10), nullable=False),
             )
engine = create_async_engine(DB_URL, echo=False)

router = Router(name="users")


async def get_bot(bot_token: str):
    if not isinstance(bot_token, str) and fullmatch(r"\d{10}:\w{35}", bot_token):
        raise Exception(
            "bot_token must be type of str with format 0000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA.")
    async with engine.begin() as conn:
        raw_res = await conn.execute(select(bots).where(bots.c.bot_token == bot_token))
    await engine.dispose()
    res = raw_res.fetchone()
    if res is None:
        raise Exception(f"token {bot_token} not found in database.")
    return res._mapping


def format_locales(text: str, user: User, chat: Chat, reply_to_user: User = None) -> str:
    if text is None:
        return "Empty message"
    data_dict = {"name": user.full_name,
                 "first_name": user.first_name,
                 "last_name": user.last_name,
                 "username": f"@{user.username}",
                 "user_id": user.id,
                 "chat": chat.full_name,
                 }
    if reply_to_user:
        data_dict.update({
                 "reply_name": reply_to_user.full_name,
                 "reply_first_name": reply_to_user.first_name,
                 "reply_last_name": reply_to_user.last_name,
                 "reply_username": f"@{reply_to_user.username}",
                 "reply_user_id": reply_to_user.id,
                 })
    text = text.replace("{{", "START_FLAG").replace("}}", "END_FLAG")
    for param in data_dict:
        text = text.replace("{" + str(param) + "}", str(data_dict[param]))
    text = text.replace("START_FLAG", "{{").replace("END_FLAG", "}}")
    return text


async def get_option(param: str):
    bot_info = await get_bot(TOKEN)
    options = bot_info['settings']
    if options is None:
        return None
    if param in options:
        return options[param]
    return None


@router.message(CommandStart())
async def start_cmd(message: Message):
    start_msg = await get_option("start_msg")
    web_app_button = await get_option("web_app_button")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=web_app_button, web_app=WebAppInfo(url=WEB_APP_URL))
        ]
    ])
    return await message.reply(format_locales(start_msg, message.from_user, message.chat), reply_markup=kb)


@router.message(StateFilter(None))
async def default_cmd(message: Message):
    default_msg = await get_option("default_msg")
    return await message.answer(format_locales(default_msg, message.from_user, message.chat))


async def on_start():
    logging.info("Bot online.")
    # await storage.connect()
    await dp.start_polling(bot)


if __name__ == "__main__":
    dp.include_router(router)
    for log_file in ('all.log',):
        with open(f'logs/{log_file}', 'a') as log:
            log.write(f'=============================\n'
                      f'New app session\n'
                      f'[{datetime.datetime.now()}]\n'
                      f'=============================\n')
    asyncio.run(on_start())
