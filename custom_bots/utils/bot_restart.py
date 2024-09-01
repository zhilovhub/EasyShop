from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, MenuButtonWebApp

from common_utils.config import cryptography_settings, custom_telegram_bot_settings
from common_utils.keyboards.keyboard_utils import make_webapp_info
from common_utils.token_encryptor import TokenEncryptor

from database.config import option_db
from database.models.bot_model import BotSchema

from logs.config import custom_bot_logger, extra_params


ALLOWED_UPDATES = [
    "message",
    "my_chat_member",
    "callback_query",
    "chat_member",
    "channel_post",
    "inline_query",
    "pre_checkout_query",
    "shipping_query",
]

BASE_URL = f"{custom_telegram_bot_settings.WEBHOOK_URL}:{custom_telegram_bot_settings.WEBHOOK_PORT}"
OTHER_BOTS_PATH = f"/{custom_telegram_bot_settings.WEBHOOK_LABEL}/" + "webhook/bot/{encrypted_bot_token}"

OTHER_BOTS_URL = f"{BASE_URL}{OTHER_BOTS_PATH}"


async def restart_custom_bot(bot: BotSchema, session: AiohttpSession):
    tg_bot = Bot(token=bot.token, session=session)
    bot_id = bot.bot_id

    if bot.status == "online":
        await tg_bot.delete_webhook(drop_pending_updates=True)
        custom_bot_logger.debug(f"bot_id={bot_id}: webhook is deleted", extra=extra_params(bot_id=bot_id))

        token_encryptor: TokenEncryptor = TokenEncryptor(cryptography_settings.TOKEN_SECRET_KEY)
        result = await tg_bot.set_webhook(
            OTHER_BOTS_URL.format(encrypted_bot_token=token_encryptor.encrypt_token(bot_token=bot.token)),
            allowed_updates=ALLOWED_UPDATES,
        )
        if result:
            custom_bot_logger.debug(f"bot_id={bot_id}: webhook is set", extra=extra_params(bot_id=bot_id))

            bot_options = await option_db.get_option(bot.options_id)

            commands = []
            if len(bot_options.languages):
                commands.append(BotCommand(command="lang", description="select language"))

            if commands:
                await tg_bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())
            else:
                await tg_bot.delete_my_commands()

            await tg_bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text="Catalog", web_app=make_webapp_info(bot_id))
            )
        else:
            custom_bot_logger.warning(
                f"bot_id={bot_id}: webhook's setting is failed", extra=extra_params(bot_id=bot_id)
            )
