from aiogram import Bot

from custom_bots.multibot import bot_db

from database.models.bot_model import BotNotFound

from logs.config import custom_bot_logger, extra_params


async def get_option(param: str, token: str):
    try:
        bot_info = await bot_db.get_bot_by_token(token)
    except BotNotFound:
        custom_bot_logger.warning(
            f"bot_token={token}: this bot is not in db. Deleting webhook...",
            extra=extra_params(bot_token=token)
        )
        return await Bot(token).delete_webhook()

    options = bot_info.settings
    if options is None:
        custom_bot_logger.warning(
            f"bot_id={bot_info.bot_id}: bot has empty settings",
            extra=extra_params(bot_id=bot_info.bot_id)
        )
        return None

    if param in options:
        return options[param]

    custom_bot_logger.warning(
        f"bot_id={bot_info.bot_id}: {param} not in settings",
        extra=extra_params(bot_id=bot_info.bot_id)
    )
    return None