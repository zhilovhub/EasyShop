import asyncio
import ssl

from aiohttp import web

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.webhook.aiohttp_server import (
    TokenBasedRequestHandler,
    setup_application,
)

from common_utils.bot_settings_config import BOT_PROPERTIES
from common_utils.env_config import TIMEZONE, SCHEDULER_URL, WEBHOOK_URL, WEBHOOK_PORT, TELEGRAM_TOKEN, WEB_APP_URL, \
    WEB_APP_PORT, RESOURCES_PATH, SSL_CERT_PATH, API_HOST, API_PORT, \
    SSL_KEY_PATH, TECH_ADMINS, LOCAL_API_SERVER_OUTSIDE, LOCAL_API_SERVER_PORT, WEBHOOK_HOST, \
    WEBHOOK_SERVER_PORT_TO_REDIRECT, WEBHOOK_LABEL, WEBHOOK_SERVER_HOST_TO_REDIRECT
from common_utils.start_message import send_start_message_to_admins
from common_utils.scheduler.scheduler import Scheduler
from common_utils.cache_json.cache_json import JsonStore
from common_utils.storage.custom_bot_storage import custom_bot_storage

from logs.config import custom_bot_logger, extra_params

app = web.Application()

local_app = web.Application(logger=custom_bot_logger)

main_router = Router()

BASE_URL = f"{WEBHOOK_URL}:{WEBHOOK_PORT}"
OTHER_BOTS_PATH = f"/{WEBHOOK_LABEL}/" + "webhook/bot/{bot_token}"

session = AiohttpSession()

main_bot = Bot(TELEGRAM_TOKEN, default=BOT_PROPERTIES, session=session)

OTHER_BOTS_URL = f"{BASE_URL}{OTHER_BOTS_PATH}"

FULL_WEB_APP_URL = f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id=[bot_id]"

API_URL = f"https://ezbots.ru:{API_PORT}"

PREV_ORDER_MSGS = JsonStore(
    file_path="prev_orders_msg_id.json", json_store_name="PREV_ORDER_MSGS")
QUESTION_MESSAGES = JsonStore(
    file_path=RESOURCES_PATH.format("question_messages.json"),
    json_store_name="QUESTION_MESSAGES"
)

scheduler = Scheduler(
    SCHEDULER_URL,
    "postgres",
    TIMEZONE,
    tablename="custom_bot_apscheduler_jobs",
    unique_id="multi_bot"
)


class CustomUserStates(StatesGroup):
    MAIN_MENU = State()
    WAITING_FOR_QUESTION = State()
    WAITING_FOR_REVIEW_MARK = State()
    WAITING_FOR_REVIEW_TEXT = State()


async def main():
    from custom_bots.handlers import multi_bot_router, multi_bot_channel_router, inline_mode_router

    multibot_dispatcher = Dispatcher(storage=custom_bot_storage)

    multibot_dispatcher.include_router(multi_bot_channel_router)
    multibot_dispatcher.include_router(multi_bot_router)
    multibot_dispatcher.include_router(inline_mode_router)

    TokenBasedRequestHandler(
        dispatcher=multibot_dispatcher,
        bot_settings={"parse_mode": ParseMode.HTML},
        session=session,
    ).register(app, path=OTHER_BOTS_PATH)

    setup_application(app, multibot_dispatcher)

    from local_api.router import routes

    local_app.add_routes(routes)

    custom_bot_logger.debug("[1/3] Routes added, application is being setup")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)  # noqa
    ssl_context.load_cert_chain(SSL_CERT_PATH, SSL_KEY_PATH)

    custom_bot_logger.debug("[2/3] SSL certificates are downloaded")

    await custom_bot_storage.connect()

    custom_bot_logger.debug(
        f"[3/3] Setting up local api server on {LOCAL_API_SERVER_OUTSIDE}:{LOCAL_API_SERVER_PORT}")
    custom_bot_logger.info(
        f"[3/3] Setting up webhook server on {WEBHOOK_HOST}:{WEBHOOK_SERVER_PORT_TO_REDIRECT} "
        f"<- {WEBHOOK_PORT}")

    await scheduler.start()

    await asyncio.gather(
        web._run_app(  # noqa
            local_app,
            host=LOCAL_API_SERVER_OUTSIDE,
            port=LOCAL_API_SERVER_PORT,
            access_log=custom_bot_logger,
            print=custom_bot_logger.debug
        ),
        web._run_app(  # noqa
            app,
            host=WEBHOOK_SERVER_HOST_TO_REDIRECT,
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
