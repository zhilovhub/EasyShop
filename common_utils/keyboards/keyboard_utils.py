from aiogram import Bot
from aiogram.types import WebAppInfo

from common_utils.env_config import WEB_APP_URL, WEB_APP_PORT

from database.config import bot_db, channel_db, channel_post_db, contest_db, post_message_db, mailing_db
from database.models.channel_model import ChannelSchema
from database.models.mailing_model import MailingSchema, MailingNotFound
from database.models.contest_model import ContestSchema, ContestNotFound
from database.models.channel_post_model import ChannelPostSchema, ChannelPostNotFound
from database.models.post_message_model import PostMessageSchema, PostMessageNotFound, PostMessageType

from logs.config import logger, extra_params


def make_webapp_info(bot_id: int) -> WebAppInfo:
    return WebAppInfo(url=f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id={bot_id}")


async def get_bot_username(bot_id: int) -> str:
    custom_bot_username = (await Bot((await bot_db.get_bot(bot_id=bot_id)).token).get_me()).username
    return custom_bot_username


async def get_bot_status(bot_id: int) -> str:
    return (await bot_db.get_bot(bot_id=int(bot_id))).status


async def get_bot_channels(bot_id: int) -> list[tuple[ChannelSchema, str]]:
    custom_bot = Bot((await bot_db.get_bot(bot_id=bot_id)).token)
    return [(i, (await custom_bot.get_chat(i.channel_id)).username)
            for i in (await channel_db.get_all_channels(bot_id=bot_id))]


async def get_bot_channel_post(bot_id: int) -> ChannelPostSchema | None:
    try:
        channel_post = await channel_post_db.get_channel_post_by_bot_id(bot_id=bot_id)
        return channel_post
    except ChannelPostNotFound:
        logger.debug(
            f"bot_id={bot_id}: there is no channel posts",
            extra=extra_params(bot_id=bot_id),
        )
        return None


async def get_bot_mailing(bot_id: int) -> MailingSchema | None:
    try:
        mailing = await mailing_db.get_mailing_by_bot_id(bot_id=bot_id)
        return mailing
    except MailingNotFound:
        logger.debug(
            f"bot_id={bot_id}: there is no mailings",
            extra=extra_params(bot_id=bot_id),
        )
        return None


async def get_bot_contest(bot_id: int) -> ContestSchema | None:
    try:
        contest = await contest_db.get_contest_by_bot_id(bot_id=bot_id)
        return contest
    except ContestNotFound:
        logger.debug(
            f"bot_id={bot_id}: there is no contests",
            extra=extra_params(bot_id=bot_id),
        )
        return None


async def get_bot_post_message(bot_id: int, post_message_type: PostMessageType) -> PostMessageSchema | None:
    try:
        post_message = await post_message_db.get_post_message_by_bot_id(bot_id, post_message_type)
        return post_message
    except PostMessageNotFound as e:
        logger.warning(
            f"bot_id={bot_id}: there is no post_message",
            extra=extra_params(bot_id=bot_id),
            exc_info=e
        )
        return None


def callback_json_validator(func):
    def wrapper_func(*args, **kwargs):
        callback_json = func(*args, **kwargs)

        if len(callback_json) > 64:
            logger.warning(f"The callback {callback_json} has len ({len(callback_json)}) more than 64")

        return callback_json

    return wrapper_func
