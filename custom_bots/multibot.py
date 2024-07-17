import asyncio
import ssl

from typing import Any, Dict, Union

from aiohttp import web

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.types import User, Chat
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.utils.token import TokenValidationError, validate_token
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.webhook.aiohttp_server import (
    TokenBasedRequestHandler,
    setup_application,
)

from common_utils.bot_settings_config import BOT_PROPERTIES
from common_utils.env_config import TIMEZONE, SCHEDULER_URL, WEBHOOK_URL, WEBHOOK_PORT, TELEGRAM_TOKEN, WEB_APP_URL, \
    WEB_APP_PORT, RESOURCES_PATH, SSL_CERT_PATH, \
    SSL_KEY_PATH, TECH_ADMINS, LOCAL_API_SERVER_HOST, LOCAL_API_SERVER_PORT, WEBHOOK_HOST, \
    WEBHOOK_SERVER_PORT_TO_REDIRECT
from common_utils.start_message import send_start_message_to_admins
from common_utils.scheduler.scheduler import Scheduler
from common_utils.cache_json.cache_json import JsonStore
from common_utils.storage.custom_bot_storage import custom_bot_storage

from database.config import bot_db
from database.models.bot_model import BotNotFound

from logs.config import custom_bot_logger, extra_params

app = web.Application()

local_app = web.Application(logger=custom_bot_logger)

routes = web.RouteTableDef()

main_router = Router()

BASE_URL = f"{WEBHOOK_URL}:{WEBHOOK_PORT}"
OTHER_BOTS_PATH = "/webhook/bot/{bot_token}"

session = AiohttpSession()

main_bot = Bot(TELEGRAM_TOKEN, default=BOT_PROPERTIES, session=session)

OTHER_BOTS_URL = f"{BASE_URL}{OTHER_BOTS_PATH}"

FULL_WEB_APP_URL = f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id=[bot_id]"

PREV_ORDER_MSGS = JsonStore(
    file_path="prev_orders_msg_id.json", json_store_name="PREV_ORDER_MSGS")
QUESTION_MESSAGES = JsonStore(
    file_path=RESOURCES_PATH.format("question_messages.json"),
    json_store_name="QUESTION_MESSAGES"
)

scheduler = Scheduler(SCHEDULER_URL, "postgres", TIMEZONE)


class CustomUserStates(StatesGroup):
    MAIN_MENU = State()
    WAITING_FOR_QUESTION = State()
    WAITING_FOR_REVIEW_MARK = State()
    WAITING_FOR_REVIEW_TEXT = State()


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
    custom_bot_logger.debug(
        f"bot_id={bot_id}: webhook is deleted",
        extra=extra_params(bot_id=bot_id)
    )

    result = await new_bot.set_webhook(
        OTHER_BOTS_URL.format(bot_token=bot.token),
        allowed_updates=["message", "my_chat_member",
                         "callback_query", "chat_member", "channel_post"]
    )
    if result:
        custom_bot_logger.debug(
            f"bot_id={bot_id}: webhook is set",
            extra=extra_params(bot_id=bot_id)
        )
    else:
        custom_bot_logger.warning(
            f"bot_id={bot_id}: webhook's setting is failed",
            extra=extra_params(bot_id=bot_id)
        )

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
    custom_bot_logger.debug(
        f"bot_id={bot_id}: webhook is deleted",
        extra=extra_params(bot_id=bot_id)
    )

    return web.Response(text=f"Stopped bot with token ({bot.token}) and username (@{new_bot_data.username})")


def is_bot_token(value: str) -> Union[bool, Dict[str, Any]]:
    try:
        validate_token(value)
    except TokenValidationError:
        return False
    return True


async def main():
    from custom_bots.handlers import multi_bot_router, multi_bot_channel_router

    multibot_dispatcher = Dispatcher(storage=custom_bot_storage)

    multibot_dispatcher.include_router(multi_bot_channel_router)
    multibot_dispatcher.include_router(multi_bot_router)

    TokenBasedRequestHandler(
        dispatcher=multibot_dispatcher,
        bot_settings=bot_settings,
        session=session,
    ).register(app, path=OTHER_BOTS_PATH)

    setup_application(app, multibot_dispatcher)

    local_app.add_routes(routes)

    custom_bot_logger.debug("[1/3] Routes added, application is being setup")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)  # noqa
    ssl_context.load_cert_chain(SSL_CERT_PATH, SSL_KEY_PATH)

    custom_bot_logger.debug("[2/3] SSL certificates are downloaded")

    await custom_bot_storage.connect()

    custom_bot_logger.debug(
        f"[3/3] Setting up local api server on {LOCAL_API_SERVER_HOST}:{LOCAL_API_SERVER_PORT}")
    custom_bot_logger.info(
        f"[3/3] Setting up webhook server on {WEBHOOK_HOST}:{WEBHOOK_SERVER_PORT_TO_REDIRECT} "
        f"<- {WEBHOOK_PORT}")

    await scheduler.start()

    await asyncio.gather(
        web._run_app(  # noqa
            local_app,
            host=LOCAL_API_SERVER_HOST,
            port=LOCAL_API_SERVER_PORT,
            access_log=custom_bot_logger,
            print=custom_bot_logger.debug
        ),
        web._run_app(  # noqa
            app,
            host=WEBHOOK_HOST,
            port=WEBHOOK_SERVER_PORT_TO_REDIRECT,
            ssl_context=ssl_context,
            access_log=custom_bot_logger,
            print=custom_bot_logger.debug
        ),
        send_start_message_to_admins(Bot(TELEGRAM_TOKEN), TECH_ADMINS, "Custom bots started!")
    )


if __name__ == "__main__":
    custom_bot_logger.debug("===== New multibot app session =====\n\n\n\n")
    asyncio.run(main())
