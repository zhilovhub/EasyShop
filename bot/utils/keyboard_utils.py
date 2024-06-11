from aiogram import Bot
from aiogram.types import WebAppInfo

from database.models.channel_post_model import ChannelPostNotFound, ChannelPostSchema
from bot.main import bot_db, channel_db, mailing_db, competition, channel_post_db
from bot.config import WEB_APP_URL, WEB_APP_PORT
from database.models.channel_model import ChannelNotFound, ChannelSchema
from database.models.competition_model import CompetitionSchema
from database.models.mailing_model import MailingSchema, MailingNotFound


def make_webapp_info(bot_id: int) -> WebAppInfo:
    return WebAppInfo(url=f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id={bot_id}")


async def get_bot_username(bot_id: int) -> str:
    custom_bot_username = (await Bot((await bot_db.get_bot(bot_id=bot_id)).token).get_me()).username
    return custom_bot_username


async def get_bot_status(bot_id: int) -> str:
    return (await bot_db.get_bot(bot_id=bot_id)).status


async def get_bot_channels(bot_id: int) -> list[tuple[ChannelSchema, str]]:
    custom_bot = Bot((await bot_db.get_bot(bot_id=bot_id)).token)
    return [(i, (await custom_bot.get_chat(i.channel_id)).username) for i in (await channel_db.get_all_channels(bot_id=bot_id))]


async def get_bot_mailing(bot_id: int) -> MailingSchema | None:
    try:
        mailing = await mailing_db.get_mailing_by_bot_id(bot_id=bot_id)
        return mailing
    except MailingNotFound:
        return None


async def get_channel_post(channel_id: int) -> ChannelPostSchema | None:
    try:
        channel_post = await channel_post_db.get_channel_post(channel_id=channel_id)
        return channel_post
    except ChannelPostNotFound:
        return None


async def get_bot_competitions(channel_id: int, bot_id: int) -> list[CompetitionSchema]:
    return await competition.get_all_competitions(channel_id, bot_id)
