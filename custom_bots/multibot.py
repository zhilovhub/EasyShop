import asyncio
import ssl

from aiohttp import web

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.webhook.aiohttp_server import (
    setup_application,
)

from common_utils.bot_settings_config import BOT_PROPERTIES
from common_utils.config import (
    custom_telegram_bot_settings,
    main_telegram_bot_settings,
    api_settings,
    common_settings,
    database_settings,
)
from common_utils.start_message import send_start_message_to_admins
from common_utils.scheduler.scheduler import Scheduler
from common_utils.cache_json.cache_json import JsonStore
from common_utils.storage.custom_bot_storage import custom_bot_storage

from custom_bots.utils.multi_dispathcer_server import EncryptedTokenBasedRequestHandler

from logs.config import custom_bot_logger

app = web.Application()

local_app = web.Application(logger=custom_bot_logger)

main_router = Router()

BASE_URL = f"{custom_telegram_bot_settings.WEBHOOK_URL}:{custom_telegram_bot_settings.WEBHOOK_PORT}"
OTHER_BOTS_PATH = f"/{custom_telegram_bot_settings.WEBHOOK_LABEL}/" + "webhook/bot/{encrypted_bot_token}"

session = AiohttpSession()

main_bot = Bot(main_telegram_bot_settings.TELEGRAM_TOKEN, default=BOT_PROPERTIES, session=session)

OTHER_BOTS_URL = f"{BASE_URL}{OTHER_BOTS_PATH}"

FULL_WEB_APP_URL = (
    f"{custom_telegram_bot_settings.WEB_APP_URL}:"
    f"{custom_telegram_bot_settings.WEB_APP_PORT}/products-page/?bot_id=[bot_id]"
)

API_URL = f"https://ezbots.ru:{api_settings.API_PORT}/api"

PREV_ORDER_MSGS = JsonStore(file_path="prev_orders_msg_id.json", json_store_name="PREV_ORDER_MSGS")
QUESTION_MESSAGES = JsonStore(
    file_path=common_settings.RESOURCES_PATH.format("question_messages.json"), json_store_name="QUESTION_MESSAGES"
)

scheduler = Scheduler(
    database_settings.SCHEDULER_URL,
    "postgres",
    database_settings.TIMEZONE,
    tablename="custom_bot_apscheduler_jobs",
    unique_id="multi_bot",
)


class CustomUserStates(StatesGroup):
    MAIN_MENU = State()
    WAITING_FOR_QUESTION = State()
    WAITING_FOR_REVIEW_MARK = State()
    WAITING_FOR_REVIEW_TEXT = State()


async def main():
    from custom_bots.handlers import multi_bot_router, multi_bot_channel_router, inline_mode_router, payment_router

    multibot_dispatcher = Dispatcher(storage=custom_bot_storage)

    multibot_dispatcher.include_router(payment_router)
    multibot_dispatcher.include_router(multi_bot_channel_router)
    multibot_dispatcher.include_router(multi_bot_router)
    multibot_dispatcher.include_router(inline_mode_router)

    EncryptedTokenBasedRequestHandler(
        dispatcher=multibot_dispatcher,
        bot_settings={"default": BOT_PROPERTIES},
        session=session,
    ).register(app, path=OTHER_BOTS_PATH)

    setup_application(app, multibot_dispatcher)

    from local_api.router import routes

    local_app.add_routes(routes)

    custom_bot_logger.debug("[1/3] Routes added, application is being setup")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)  # noqa
    ssl_context.load_cert_chain(api_settings.SSL_CERT_PATH, api_settings.SSL_KEY_PATH)

    custom_bot_logger.debug("[2/3] SSL certificates are downloaded")

    await custom_bot_storage.connect()

    custom_bot_logger.debug(
        f"[3/3] Setting up local api server on "
        f"{custom_telegram_bot_settings.WEBHOOK_LOCAL_API_URL_OUTSIDE}:"
        f"{custom_telegram_bot_settings.WEBHOOK_LOCAL_API_PORT}"
    )
    custom_bot_logger.info(
        f"[3/3] Setting up webhook server on "
        f"{custom_telegram_bot_settings.WEBHOOK_HOST}:"
        f"{custom_telegram_bot_settings.WEBHOOK_SERVER_PORT_TO_REDIRECT} "
        f"<- {custom_telegram_bot_settings.WEBHOOK_PORT}"
    )

    await scheduler.start()

    await asyncio.gather(
        web._run_app(  # noqa
            local_app,
            host=custom_telegram_bot_settings.WEBHOOK_LOCAL_API_URL_OUTSIDE,
            port=custom_telegram_bot_settings.WEBHOOK_LOCAL_API_PORT,
            access_log=custom_bot_logger,
            print=custom_bot_logger.debug,
        ),
        web._run_app(  # noqa
            app,
            host=custom_telegram_bot_settings.WEBHOOK_SERVER_HOST_TO_REDIRECT,
            port=custom_telegram_bot_settings.WEBHOOK_SERVER_PORT_TO_REDIRECT,
            ssl_context=ssl_context,
            access_log=custom_bot_logger,
            print=custom_bot_logger.debug,
        ),
        send_start_message_to_admins(
            Bot(main_telegram_bot_settings.TELEGRAM_TOKEN), common_settings.TECH_ADMINS, "Custom bots started!"
        ),
    )


if __name__ == "__main__":
    custom_bot_logger.debug("===== New multibot app session =====\n\n\n\n")
    asyncio.run(main())
