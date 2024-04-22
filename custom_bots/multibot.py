import logging
import sys
import time
from os import getenv
from typing import Any, Dict, Union
from datetime import datetime

import asyncio

from aiohttp import web
import ssl

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from bot.utils.storage import AlchemyStorageAsync
from aiogram.types import Message, User, Chat, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.token import TokenValidationError, validate_token
from aiogram.exceptions import TelegramUnauthorizedError, TelegramAPIError
from aiogram.client.default import DefaultBotProperties

from bot.middlewaries.errors_middleware import ErrorMiddleware

from aiogram.webhook.aiohttp_server import (
    TokenBasedRequestHandler,
    setup_application,
)

from database.models.custom_bot_user_model import CustomBotUserNotFound
from database.models.models import Database
from database.models.bot_model import BotNotFound
from database.models.order_model import OrderSchema, OrderStatusValues, OrderNotFound

from bot import config
from bot.utils import JsonStore
from bot.keyboards import keyboards

import json

from dotenv import load_dotenv

app = web.Application()

local_app = web.Application()

routes = web.RouteTableDef()

load_dotenv()

main_router = Router()

WEBHOOK_SERVER_URL = getenv("WEBHOOK_URL")
WEBHOOK_SERVER_HOST = getenv("WEBHOOK_HOST")
WEBHOOK_SERVER_PORT = int(getenv("WEBHOOK_PORT"))

BASE_URL = f"{WEBHOOK_SERVER_URL}:{WEBHOOK_SERVER_PORT}"
OTHER_BOTS_PATH = "/webhook/bot/{bot_token}"

session = AiohttpSession()
bot_settings = {"parse_mode": ParseMode.HTML}

MAIN_TELEGRAM_TOKEN = getenv("TELEGRAM_TOKEN")
main_bot = Bot(MAIN_TELEGRAM_TOKEN, default=DefaultBotProperties(**bot_settings), session=session)

OTHER_BOTS_URL = f"{BASE_URL}{OTHER_BOTS_PATH}"

WEB_APP_URL = f"{getenv('WEB_APP_URL')}:{getenv('WEB_APP_PORT')}/products-page/?bot_id=[bot_id]"

LOCAL_API_SERVER_HOST = getenv("WEBHOOK_LOCAL_API_URL")
LOCAL_API_SERVER_PORT = int(getenv("WEBHOOK_LOCAL_API_PORT"))

db_engine: Database = Database(sqlalchemy_url=getenv("SQLALCHEMY_URL"))
bot_db = db_engine.get_bot_dao()
product_db = db_engine.get_product_db()
order_db = db_engine.get_order_dao()
custom_bot_user_db = db_engine.get_custom_bot_user_db()

storage = AlchemyStorageAsync(db_url=getenv("CUSTOM_BOT_STORAGE_DB_URL"),
                              table_name=getenv("CUSTOM_BOT_STORAGE_TABLE_NAME"))

multi_bot_router = Router(name="multibot")

logging.basicConfig(format=u'[%(asctime)s][%(levelname)s] ::: %(filename)s(%(lineno)d) -> %(message)s',
                    level="INFO", filename='logs/all.log')
logger = logging.getLogger('logger')

PREV_ORDER_MSGS = JsonStore(file_path="prev_orders_msg_id.json", json_store_name="PREV_ORDER_MSGS")
QUESTION_MESSAGES = JsonStore(
    file_path=config.RESOURCES_PATH.format("question_messages.json"),
    json_store_name="QUESTION_MESSAGES"
)


class CustomUserStates(StatesGroup):
    MAIN_MENU = State()
    WAITING_FOR_QUESTION = State()


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


@routes.get('/start_bot/{bot_id}')
async def add_bot_handler(request):
    bot_id = request.match_info['bot_id']
    try:
        bot = await bot_db.get_bot(int(bot_id))
    except BotNotFound:
        return web.Response(status=404, text=f"Bot with provided id not found (id: {bot_id}).")
    if not is_bot_token(bot.token):
        return web.Response(status=400, text="Incorrect bot token format.")
    try:
        new_bot = Bot(token=bot.token, session=session)
        new_bot_data = await new_bot.get_me()
    except TelegramUnauthorizedError:
        return web.Response(status=400, text="Unauthorized telegram token.")
    await new_bot.delete_webhook(drop_pending_updates=True)
    await new_bot.set_webhook(OTHER_BOTS_URL.format(bot_token=bot.token))
    return web.Response(text=f"Started bot with token ({bot.token}) and username (@{new_bot_data.username})")


@routes.get('/stop_bot/{bot_id}')
async def stop_bot_handler(request):
    bot_id = request.match_info['bot_id']
    try:
        bot = await bot_db.get_bot(int(bot_id))
    except BotNotFound:
        return web.Response(status=404, text=f"Bot with provided id not found (id: {bot_id}).")
    if not is_bot_token(bot.token):
        return web.Response(status=400, text="Incorrect bot token format.")
    try:
        new_bot = Bot(token=bot.token, session=session)
        new_bot_data = await new_bot.get_me()
    except TelegramUnauthorizedError:
        return web.Response(status=400, text="Unauthorized telegram token.")
    await new_bot.delete_webhook(drop_pending_updates=True)
    return web.Response(text=f"Stopped bot with token ({bot.token}) and username (@{new_bot_data.username})")


def is_bot_token(value: str) -> Union[bool, Dict[str, Any]]:
    try:
        validate_token(value)
    except TokenValidationError:
        return False
    return True


async def get_option(param: str, token: str):
    try:
        bot_info = await bot_db.get_bot_by_token(token)
    except BotNotFound:
        return await Bot(token).delete_webhook()

    options = bot_info.settings
    if options is None:
        return None
    if param in options:
        return options[param]
    return None


@multi_bot_router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    order_user_data = await event.bot.get_chat(user_id)

    try:
        data = json.loads(event.web_app_data.data)
        logger.info(f"receive web app data: {data}")

        order_params = ('order_id', 'products', 'payment_method', 'ordered_at', 'address', 'comment', 'bot_id')
        order_data = {k: v for k, v in data.items() if k in order_params}

        order_data["from_user"] = user_id
        order_data["payment_method"] = "Картой Онлайн"
        order_data["status"] = "backlog"
        order_data["count"] = 0

        order = OrderSchema(**order_data)

        order.from_user = user_id
        order.ordered_at = order.ordered_at.replace(tzinfo=None)
        await order_db.add_order(order)

        logger.info(f"order with id #{order.id} created")
    except Exception:
        logger.error("error while creating order", exc_info=True)
        return await event.answer("Произошла ошибка при создании заказа, попробуйте еще раз.")

    products = [(await product_db.get_product(int(product_id)), amount) for product_id, amount in
                data['products'].items()]
    username = "@" + order_user_data.username if order_user_data.username else order_user_data.full_name
    admin_id = (await bot_db.get_bot_by_token(event.bot.token)).created_by
    main_msg = await main_bot.send_message(
        admin_id, order.convert_to_notification_text(
            products,
            username,
            True
        ))

    msg_id_data = PREV_ORDER_MSGS.get_data()
    msg_id_data[order.id] = (main_msg.chat.id, main_msg.message_id)
    PREV_ORDER_MSGS.update_data(msg_id_data)
    msg = await event.bot.send_message(
        user_id, order.convert_to_notification_text(
            products,
            username,
            False
        ), reply_markup=keyboards.create_user_order_kb(order.id)
    )
    await main_bot.edit_message_reply_markup(
        main_msg.chat.id,
        main_msg.message_id,
        reply_markup=keyboards.create_change_order_status_kb(order.id, msg.message_id, msg.chat.id,
                                                             current_status=order.status)
    )


@multi_bot_router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    start_msg = await get_option("start_msg", message.bot.token)
    web_app_button = await get_option("web_app_button", message.bot.token)
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
        try:
            await custom_bot_user_db.get_custom_bot_user(bot.bot_id, message.from_user.id)
        except CustomBotUserNotFound:
            logger.info(
                f"custom_user {message.from_user.id} of bot_id {bot.bot_id} not found in db, creating new instance..."
            )
            await custom_bot_user_db.add_custom_bot_user(bot.bot_id, message.from_user.id)
    except BotNotFound:
        return await message.answer("Бот не инициализирован")

    await state.set_state(CustomUserStates.MAIN_MENU)

    return await message.answer(
        format_locales(start_msg, message.from_user, message.chat),
        reply_markup=keyboards.get_custom_bot_menu_keyboard(web_app_button, bot.bot_id)
    )


@multi_bot_router.message(CustomUserStates.MAIN_MENU)
async def default_cmd(message: Message):
    web_app_button = await get_option("web_app_button", message.bot.token)

    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
    except BotNotFound:
        return await message.answer("Бот не инициализирован")

    default_msg = await get_option("default_msg", message.bot.token)
    await message.answer(
        format_locales(default_msg, message.from_user, message.chat),
        reply_markup=keyboards.get_custom_bot_menu_keyboard(web_app_button, bot.bot_id)
    )


@multi_bot_router.callback_query(lambda q: q.data.startswith("order_"))
async def handle_order_callback(query: CallbackQuery):
    data = query.data.split(":")
    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        await query.answer("Ошибка при работе с заказом, возможно статус уже изменился", show_alert=True)
        return await query.message.edit_reply_markup(None)
    match data[0]:
        case "order_pre_cancel":
            await query.message.edit_reply_markup(reply_markup=keyboards.create_cancel_confirm_kb(data[1]))
        case "order_back_to_order":
            await query.message.edit_reply_markup(reply_markup=keyboards.create_user_order_kb(data[1]))
        case "order_cancel":
            order.status = OrderStatusValues.CANCELLED
            await order_db.update_order(order)
            products = [(await product_db.get_product(int(product_id)), amount) for product_id, amount in
                        order.products.items()]
            await query.message.edit_text(order.convert_to_notification_text(products=products), reply_markup=None)
            msg_id_data = PREV_ORDER_MSGS.get_data()
            await main_bot.edit_message_text(
                text=order.convert_to_notification_text(
                    products=products,
                    username="@" + query.from_user.username if query.from_user.username else query.from_user.full_name,
                    is_admin=True
                ), chat_id=msg_id_data[order.id][0], message_id=msg_id_data[order.id][1], reply_markup=None)
            await main_bot.send_message(
                chat_id=msg_id_data[order.id][0],
                text=f"Новый статус заказа <b>#{order.id}</b>\n<b>{order.translate_order_status()}</b>")
            del msg_id_data[order.id]


@multi_bot_router.callback_query(lambda q: q.data.startswith("ask_question"))
async def handle_ask_question_callback(query: CallbackQuery, state: FSMContext):
    data = query.data.split(":")

    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        await query.answer("Ошибка при работе с заказом, возможно заказ был удалён", show_alert=True)
        return await query.message.edit_reply_markup(None)

    state_data = await state.get_data()
    if not state_data:
        state_data = {"order_id": order.id}
    else:
        if "last_question_time" in state_data and time.time() - state_data['last_question_time'] < 1 * 60 * 60:
            return await query.answer("Вы уже задавали вопрос недавно, пожалуйста, попробуйте позже "
                                      "(между вопросами должен пройти час)", show_alert=True)
        state_data['order_id'] = order.id

    await state.set_state(CustomUserStates.WAITING_FOR_QUESTION)
    await query.message.answer(
        "Вы можете отправить свой вопрос по заказу, отправив любое сообщение боту",
        reply_markup=keyboards.get_back_keyboard()
    )
    await state.set_data(state_data)


@multi_bot_router.message(CustomUserStates.WAITING_FOR_QUESTION)
async def handle_waiting_for_question_state(message: Message, state: FSMContext):
    state_data = await state.get_data()

    if not state_data or 'order_id' not in state_data:
        await state.set_state(CustomUserStates.MAIN_MENU)
        return await message.answer("Произошла ошибка возвращаюсь в главное меню...")

    await message.reply(f"Вы уверены что хотите отправить это сообщение вопросом к заказу "
                        f"<b>#{state_data['order_id']}</b>?"
                        f"\n\nПосле отправки вопроса, Вы сможете отправить следующий <b>минимум через 1 час</b> или "
                        f"<b>после ответа администратора</b>",
                        reply_markup=keyboards.create_confirm_question_kb(
                            order_id=state_data['order_id'],
                            msg_id=message.message_id,
                            chat_id=message.chat.id
                        ))


@multi_bot_router.callback_query(lambda q: q.data.startswith("approve_ask_question"))
async def approve_ask_question_callback(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()

    if not state_data or 'order_id' not in state_data:
        await state.set_state(CustomUserStates.MAIN_MENU)
        await query.message.edit_reply_markup(None)
        return await query.answer("Произошла ошибка возвращаюсь в главное меню...", show_alert=True)

    data = query.data.split(":")
    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        await query.answer("Ошибка при работе с заказом, возможно заказ был удалён", show_alert=True)
        return await query.message.edit_reply_markup(None)

    bot_data = await bot_db.get_bot_by_token(query.bot.token)
    try:
        message = await main_bot.send_message(chat_id=bot_data.created_by,
                                              text=f"Новый вопрос по заказу <b>#{order.id}</b> от пользователя "
                                                   f"<b>{'@' + query.from_user.username if query.from_user.username else query.from_user.full_name}</b> 👇\n\n"
                                                   f"<i>{query.message.reply_to_message.text}</i>\n\n"
                                                   f"Для ответа на вопрос <b>зажмите это сообщение</b> и ответьте на него")
        question_messages_data = QUESTION_MESSAGES.get_data()
        question_messages_data[message.message_id] = {
            "question_from_custom_bot_message_id": data[2],
            "order_id": order.id
        }
        QUESTION_MESSAGES.update_data(question_messages_data)
    except TelegramAPIError:
        await main_bot.send_message(chat_id=bot_data.created_by,
                                    text="Вам поступило новое <b>сообщение-вопрос</b> от клиента, "
                                         "но Вашему боту <b>не удалось Вам его отправить</b>, "
                                         "проверьте писали ли Вы хоть раз своему боту и не заблокировали ли вы его"
                                         f"\n\n* ссылка на Вашего бота @{(await query.bot.get_me()).username}")

        logger.info("cant send order question to admin", exc_info=True)
        await state.set_state(CustomUserStates.MAIN_MENU)
        return await query.answer(":( Не удалось отправить Ваш вопрос", show_alert=True)

    await query.message.edit_text(
        "Ваш вопрос отправлен, ожидайте ответа от администратора магазина в этом чате", reply_markup=None
    )

    state_data['last_question_time'] = time.time()

    await state.set_state(CustomUserStates.MAIN_MENU)
    await state.set_data(state_data)


@multi_bot_router.callback_query(lambda q: q.data.startswith("cancel_ask_question"))
async def cancel_ask_question_callback(query: CallbackQuery, state: FSMContext):
    await query.answer("Отправка вопроса администратору отменена\nВозвращаемся в меню", show_alert=True)
    await state.set_state(CustomUserStates.MAIN_MENU)
    await query.message.edit_reply_markup(reply_markup=None)


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    multibot_dispatcher = Dispatcher(storage=storage)

    multibot_dispatcher.include_router(multi_bot_router)

    multi_bot_router.message.middleware(ErrorMiddleware())
    multi_bot_router.callback_query.middleware(ErrorMiddleware())

    TokenBasedRequestHandler(
        dispatcher=multibot_dispatcher,
        bot_settings=bot_settings,
        session=session,
    ).register(app, path=OTHER_BOTS_PATH)

    setup_application(app, multibot_dispatcher)

    local_app.add_routes(routes)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(getenv('SSL_CERT_PATH'), getenv('SSL_KEY_PATH'))

    logger.info(f"setting up local api server on {LOCAL_API_SERVER_HOST}:{LOCAL_API_SERVER_PORT}")
    logger.info(f"setting up webhook server on {WEBHOOK_SERVER_HOST}:{WEBHOOK_SERVER_PORT}")

    await storage.connect()

    await asyncio.gather(
        web._run_app(local_app, host=LOCAL_API_SERVER_HOST, port=LOCAL_API_SERVER_PORT),
        web._run_app(app, host=WEBHOOK_SERVER_HOST, port=WEBHOOK_SERVER_PORT, ssl_context=ssl_context)
    )


if __name__ == "__main__":
    for log_file in ('all.log', 'err.log'):
        with open(f'logs/{log_file}', 'a') as log:
            log.write(f'=============================\n'
                      f'New multibot app session\n'
                      f'[{datetime.now()}]\n'
                      f'=============================\n')
    asyncio.run(main())
