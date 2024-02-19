import json
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
from aiogram.types import Message, Chat, User, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.web_app_info import WebAppInfo

from aiogram import F

from database.models.models import Database
from database.models.order_model import OrderNotFound, OrderStatusValues, OrderSchema

from bot.keyboards import keyboards

dotenv.load_dotenv()

MAIN_TELEGRAM_TOKEN = os.getenv("MAIN_TELEGRAM_TOKEN")
TOKEN = os.getenv("CUSTOM_TELEGRAM_TOKEN")
DB_URL = os.getenv("DB_URL")
WEB_APP_URL = os.getenv("CUSTOM_WEB_APP_URL")

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db_engine = Database(sqlalchemy_url=DB_URL)
bot_db = db_engine.get_bot_dao()
product_db = db_engine.get_product_db()
order_db = db_engine.get_order_dao()
PREV_ORDER_MSGS = {}

logging.basicConfig(format=u'[%(asctime)s][%(levelname)s] ::: %(filename)s(%(lineno)d) -> %(message)s',
                    level="INFO", filename='logs/all.log')
logger = logging.getLogger('logger')

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
    bot_info = await bot_db.get_bot(TOKEN)
    options = bot_info.settings
    if options is None:
        return None
    if param in options:
        return options[param]
    return None


@router.message(CommandStart())
async def start_cmd(message: Message):
    start_msg = await get_option("start_msg")
    web_app_button = await get_option("web_app_button")
    kb = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text=web_app_button, web_app=WebAppInfo(url=WEB_APP_URL))
        ]
    ], resize_keyboard=True)
    return await message.reply(format_locales(start_msg, message.from_user, message.chat), reply_markup=kb)


@router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    order_user_data = await bot.get_chat(user_id)

    try:
        data = json.loads(event.web_app_data.data)
        logger.info(f"receive web app data: {data}")

        data["from_user"] = user_id
        data["status"] = "backlog"

        order = OrderSchema(**data)

        order.from_user = user_id
        await order_db.add_order(order)

        logger.info(f"order with id #{order.id} created")
    except Exception:
        logger.error("error while creating order", exc_info=True)
        return await event.answer("Произошла ошибка при создании заказа, попробуйте еще раз.")

    products = [await product_db.get_product(product_id) for product_id in order.products_id]
    username = "@" + order_user_data.username if order_user_data.username else order_user_data.full_name
    admin_id = (await bot_db.get_bot(TOKEN)).created_by
    main_msg = await Bot(MAIN_TELEGRAM_TOKEN, parse_mode=ParseMode.HTML).send_message(
        admin_id, order.convert_to_notification_text(
            products,
            username,
            True
        ))

    PREV_ORDER_MSGS[order.id] = (main_msg.chat.id, main_msg.message_id)
    msg = await bot.send_message(
        user_id, order.convert_to_notification_text(
            products,
            username,
            False
        ), reply_markup=keyboards.create_cancel_order_kb(order.id)
    )
    await Bot(MAIN_TELEGRAM_TOKEN, parse_mode=ParseMode.HTML).edit_message_reply_markup(
        main_msg.chat.id,
        main_msg.message_id,
        reply_markup=keyboards.create_change_order_status_kb(order.id, False, msg.message_id, msg.chat.id)
    )


@router.message(StateFilter(None))
async def default_cmd(message: Message):
    web_app_button = await get_option("web_app_button")
    kb = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text=web_app_button, web_app=WebAppInfo(url=WEB_APP_URL))
        ]
    ], resize_keyboard=True)
    default_msg = await get_option("default_msg")
    await message.answer(format_locales(default_msg, message.from_user, message.chat), reply_markup=kb)


@router.callback_query(lambda q: q.data.startswith("order_"))
async def handle_callback(query: CallbackQuery):
    data = query.data.split(":")
    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        await query.answer("Ошибка при работе с заказом, возможно статус уже изменился.", show_alert=True)
        return await query.message.edit_reply_markup(None)
    match data[0]:
        case "order_pre_cancel":
            await query.message.edit_reply_markup(reply_markup=keyboards.create_cancel_confirm_kb(data[1]))
        case "order_back_to_order":
            await query.message.edit_reply_markup(reply_markup=keyboards.create_cancel_order_kb(data[1]))
        case "order_cancel":
            order.status = OrderStatusValues.CANCELLED
            await order_db.update_order(order)
            products = [await product_db.get_product(product_id) for product_id in order.products_id]
            await query.message.edit_text(order.convert_to_notification_text(products=products), reply_markup=None)
            await Bot(MAIN_TELEGRAM_TOKEN, parse_mode=ParseMode.HTML).edit_message_text(
                text=order.convert_to_notification_text(
                    products=products,
                    username="@" + query.from_user.username if query.from_user.username else query.from_user.full_name,
                    is_admin=True
                ), chat_id=PREV_ORDER_MSGS[order.id][0], message_id=PREV_ORDER_MSGS[order.id][1], reply_markup=None)
            await Bot(MAIN_TELEGRAM_TOKEN, parse_mode=ParseMode.HTML).send_message(
                chat_id=PREV_ORDER_MSGS[order.id][0],
                text=f"Новый статус заказа <b>#{order.id}</b>\n<b>{order.translate_order_status()}</b>")
            del PREV_ORDER_MSGS[order.id]


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
