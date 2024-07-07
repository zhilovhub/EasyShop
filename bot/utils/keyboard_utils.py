from aiogram import Bot
from aiogram.types import WebAppInfo

from bot.main import bot_db, channel_db, post_message_db, mailing_db, channel_post_db, product_db
from bot.config import WEB_APP_URL, WEB_APP_PORT
from bot.enums.post_message_type import PostMessageType

from database.models.channel_model import ChannelSchema
from database.models.mailing_model import MailingSchema, MailingNotFound
from database.models.product_model import ProductSchema, ProductNotFound
from database.models.channel_post_model import ChannelPostSchema, ChannelPostNotFound
from database.models.post_message_model import PostMessageSchema, PostMessageNotFound

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


async def get_bot_post_message(bot_id: int, post_message_type: PostMessageType) -> PostMessageSchema | None:
    try:
        post_message = await post_message_db.get_post_message_by_bot_id(bot_id, post_message_type)
        return post_message
    except PostMessageNotFound:
        logger.debug(
            f"bot_id={bot_id}: there is no post_message",
            extra=extra_params(bot_id=bot_id),
        )
        return None


async def get_product_by_id(product_id: int) -> ProductSchema | None:
    try:
        product = await product_db.get_product(product_id=product_id)
        return product
    except ProductNotFound:
        logger.debug(
            f"product_id={product_id}: not found",
            extra=extra_params(product_id=product_id)
        )
        return None
