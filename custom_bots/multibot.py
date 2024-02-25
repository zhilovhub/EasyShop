import logging
import sys
from os import getenv
from typing import Any, Dict, Union
from datetime import datetime

from aiohttp import web
import ssl

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.types import Message, User, Chat, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.token import TokenValidationError, validate_token
from aiogram.exceptions import TelegramUnauthorizedError
from dotenv import load_dotenv
from aiogram.webhook.aiohttp_server import (
    TokenBasedRequestHandler,
    setup_application,
)
from aiogram.types.web_app_info import WebAppInfo

from database.models.models import Database
from database.models.order_model import OrderSchema, OrderStatusValues, OrderNotFound

from bot.keyboards import keyboards

import json

app = web.Application()

routes = web.RouteTableDef()

load_dotenv()

main_router = Router()

BASE_URL = getenv("WEBHOOK_URL") + ":" + getenv("WEBHOOK_PORT")
OTHER_BOTS_PATH = "/webhook/bot/{bot_token}"

session = AiohttpSession()
bot_settings = {"session": session, "parse_mode": ParseMode.HTML}

MAIN_TELEGRAM_TOKEN = getenv("TELEGRAM_TOKEN")
main_bot = Bot(MAIN_TELEGRAM_TOKEN, **bot_settings)

OTHER_BOTS_URL = f"{BASE_URL}{OTHER_BOTS_PATH}"

WEB_APP_URL = f"{getenv('WEB_APP_URL')}?[token]"

WEB_SERVER_HOST = getenv("WEBHOOK_LOCAL_API_URL")
WEB_SERVER_PORT = int(getenv("WEBHOOK_LOCAL_API_PORT"))

db_engine = Database(sqlalchemy_url=getenv("SQLALCHEMY_URL"))
bot_db = db_engine.get_bot_dao()
product_db = db_engine.get_product_db()
order_db = db_engine.get_order_dao()

PREV_ORDER_MSGS = {}

storage = MemoryStorage()

multi_bot_router = Router(name="multibot")

logging.basicConfig(format=u'[%(asctime)s][%(levelname)s] ::: %(filename)s(%(lineno)d) -> %(message)s',
                    level="INFO", filename='logs/all.log')
logger = logging.getLogger('logger')


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


@routes.get('/start_bot/{bot_token}')
async def add_bot_handler(request):
    bot_token = request.match_info['bot_token']
    if not is_bot_token(bot_token):
        return web.Response(status=400, text="Incorrect bot token format.")
    try:
        new_bot = Bot(token=bot_token, session=session)
        new_bot_data = await new_bot.get_me()
    except TelegramUnauthorizedError:
        return web.Response(status=400, text="Unauthorized telegram token.")
    await new_bot.delete_webhook(drop_pending_updates=True)
    await new_bot.set_webhook(OTHER_BOTS_URL.format(bot_token=bot_token))
    return web.Response(text=f"Added bot with token ({bot_token}) and username (@{new_bot_data.username})")


@routes.get('/stop_bot/{bot_token}')
async def stop_bot_handler(request):
    bot_token = request.match_info['bot_token']
    if not is_bot_token(bot_token):
        return web.Response(status=400, text="Incorrect bot token format.")
    try:
        new_bot = Bot(token=bot_token, session=session)
        new_bot_data = await new_bot.get_me()
    except TelegramUnauthorizedError:
        return web.Response(status=400, text="Unauthorized telegram token.")
    await new_bot.delete_webhook(drop_pending_updates=True)
    return web.Response(text=f"Stopped bot with token ({bot_token}) and username (@{new_bot_data.username})")


def is_bot_token(value: str) -> Union[bool, Dict[str, Any]]:
    try:
        validate_token(value)
    except TokenValidationError:
        return False
    return True


# @main_router.message(Command("add", magic=F.args.func(is_bot_token)))
# async def command_add_bot(message: Message, command: CommandObject, bot: Bot) -> Any:
#     new_bot = Bot(token=command.args, session=bot.session)
#     try:
#         bot_user = await new_bot.get_me()
#     except TelegramUnauthorizedError:
#         return message.answer("Invalid token")
#     await new_bot.delete_webhook(drop_pending_updates=True)
#     await new_bot.set_webhook(OTHER_BOTS_URL.format(bot_token=command.args))
#     return await message.answer(f"Bot @{bot_user.username} successful added")


# async def on_startup(dispatcher: Dispatcher, bot: Bot):
#     await bot.set_webhook(f"{BASE_URL}{MAIN_BOT_PATH}")


async def get_option(param: str, token: str):
    bot_info = await bot_db.get_bot(token)
    options = bot_info.settings
    if options is None:
        return None
    if param in options:
        return options[param]
    return None


@multi_bot_router.message(CommandStart())
async def start_cmd(message: Message):
    start_msg = await get_option("start_msg", message.bot.token)
    web_app_button = await get_option("web_app_button", message.bot.token)
    kb = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text=web_app_button, web_app=WebAppInfo(
                url=WEB_APP_URL.replace('[token]', message.bot.token)))
        ]
    ], resize_keyboard=True)
    return await message.reply(format_locales(start_msg, message.from_user, message.chat), reply_markup=kb)


@multi_bot_router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    order_user_data = await event.bot.get_chat(user_id)

    try:
        data = json.loads(event.web_app_data.data)
        logger.info(f"receive web app data: {data}")

        data["from_user"] = user_id
        data["status"] = "backlog"

        order = OrderSchema(**data)

        order.from_user = user_id
        order.ordered_at = order.ordered_at.replace(tzinfo=None)
        await order_db.add_order(order)

        logger.info(f"order with id #{order.id} created")
    except Exception:
        logger.error("error while creating order", exc_info=True)
        return await event.answer("Произошла ошибка при создании заказа, попробуйте еще раз.")

    products = [await product_db.get_product(product_id) for product_id in order.products_id]
    username = "@" + order_user_data.username if order_user_data.username else order_user_data.full_name
    admin_id = (await bot_db.get_bot(event.bot.token)).created_by
    main_msg = await main_bot.send_message(
        admin_id, order.convert_to_notification_text(
            products,
            username,
            True
        ))

    PREV_ORDER_MSGS[order.id] = (main_msg.chat.id, main_msg.message_id)
    msg = await event.bot.send_message(
        user_id, order.convert_to_notification_text(
            products,
            username,
            False
        ), reply_markup=keyboards.create_cancel_order_kb(order.id)
    )
    await main_bot.edit_message_reply_markup(
        main_msg.chat.id,
        main_msg.message_id,
        reply_markup=keyboards.create_change_order_status_kb(order.id, msg.message_id, msg.chat.id, False)
    )


@multi_bot_router.message(StateFilter(None))
async def default_cmd(message: Message):
    web_app_button = await get_option("web_app_button", message.bot.token)
    kb = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text=web_app_button, web_app=WebAppInfo(url=WEB_APP_URL))
        ]
    ], resize_keyboard=True)
    default_msg = await get_option("default_msg", message.bot.token)
    await message.answer(format_locales(default_msg, message.from_user, message.chat), reply_markup=kb)


@multi_bot_router.callback_query(lambda q: q.data.startswith("order_"))
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
            await main_bot.edit_message_text(
                text=order.convert_to_notification_text(
                    products=products,
                    username="@" + query.from_user.username if query.from_user.username else query.from_user.full_name,
                    is_admin=True
                ), chat_id=PREV_ORDER_MSGS[order.id][0], message_id=PREV_ORDER_MSGS[order.id][1], reply_markup=None)
            await main_bot.send_message(
                chat_id=PREV_ORDER_MSGS[order.id][0],
                text=f"Новый статус заказа <b>#{order.id}</b>\n<b>{order.translate_order_status()}</b>")
            del PREV_ORDER_MSGS[order.id]


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    multibot_dispatcher = Dispatcher(storage=storage)

    multibot_dispatcher.include_router(multi_bot_router)

    TokenBasedRequestHandler(
        dispatcher=multibot_dispatcher,
        bot_settings=bot_settings,
    ).register(app, path=OTHER_BOTS_PATH)

    setup_application(app, multibot_dispatcher)

    app.add_routes(routes)

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(getenv('SSL_CERT_PATH'), getenv('SSL_KEY_PATH'))

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT, ssl_context=ssl_context)


if __name__ == "__main__":
    for log_file in ('all.log', 'err.log'):
        with open(f'logs/{log_file}', 'a') as log:
            log.write(f'=============================\n'
                      f'New multibot app session\n'
                      f'[{datetime.now()}]\n'
                      f'=============================\n')
    main()
