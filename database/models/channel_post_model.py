import datetime
from typing import Optional

from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, ForeignKeyConstraint, String, \
    DateTime, update
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.bot_model import Bot
from database.models.dao import Dao
from enum import Enum
from database.models.channel_model import Channel
from logs.config import extra_params


class ChannelPostNotFound(Exception):
    """Raised when provided ChannelPost not found in database"""
    pass


class ChannelPost(Base):
    __tablename__ = "channel_posts"

    channel_post_id = Column(BigInteger, autoincrement=True, primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id), nullable=False)
    channel_id = Column(ForeignKey(Channel.channel_id,
                        ondelete="CASCADE"), nullable=False)
    description = Column(String)
    is_sent = Column(BOOLEAN, default=False)

    has_button = Column(BOOLEAN, default=False)
    button_text = Column(String, default="Shop")
    button_url = Column(String)

    created_at = Column(DateTime, nullable=False)

    # Extra settings
    enable_notification_sound = Column(BOOLEAN, default=True)
    enable_link_preview = Column(BOOLEAN, default=False)

    # ChannelPost Stats
    is_running = Column(BOOLEAN, default=False)

    # Delay
    is_delayed = Column(BOOLEAN, default=False)
    send_date = Column(DateTime, nullable=True)
    job_id = Column(String, nullable=True)


class ChannelPostSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)
    channel_id: int = Field(frozen=True)

    description: Optional[str | None] = None
    is_sent: bool = False

    has_button: bool = False
    button_text: Optional[str | None] = None
    button_url: Optional[str | None] = None

    created_at: datetime.datetime = datetime.datetime.now().replace(tzinfo=None)

    enable_notification_sound: bool = True
    enable_link_preview: bool = False

    is_running: bool = False

    is_delayed: bool = False
    send_date: Optional[datetime.datetime | None] = None
    job_id: Optional[str | None] = None


class ChannelPostSchema(ChannelPostSchemaWithoutId):
    channel_post_id: int = Field(frozen=True)


class ChannelPostDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_channel_post(self, channel_id: int) -> ChannelPostSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(ChannelPost).where(ChannelPost.channel_id == channel_id, ChannelPost.is_sent == False))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ChannelPostNotFound

        res = ChannelPostSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: channel_post {res.channel_post_id} is found",
            extra=extra_params(
                channel_id=channel_id, bot_id=res.bot_id)
        )

        return res

    # @validate_call(validate_return=True)
    # async def get_channel_post_by_channel_id(self, channel_id: int) -> ChannelPostSchema:
    #     async with self.engine.begin() as conn:
    #         raw_res = await conn.execute(
    #             select(ChannelPost).where(ChannelPost.channel_id == channel_id, ChannelPost.is_sent == False))
    #     await self.engine.dispose()

    #     raw_res = raw_res.fetchone()
    #     if not raw_res:
    #         raise ChannelPostNotFound

    #     res = ChannelPostSchema.model_validate(raw_res)

    #     self.logger.debug(
    #         f"bot_id={res.bot_id}: channel_post {res.channel_post_id} is found",
    #         extra=extra_params(
    #             channel_post_id=res.channel_post_id, bot_id=bot_id)
    #     )

    #     return res

    @validate_call
    async def add_channel_post(self, new_channel_post: ChannelPostSchemaWithoutId) -> int:
        if type(new_channel_post) != ChannelPostSchemaWithoutId:
            raise InvalidParameterFormat(
                "new_channel_post must be type of ChannelPostSchema")

        async with self.engine.begin() as conn:
            channel_post_id = (await conn.execute(insert(ChannelPost).values(new_channel_post.model_dump()))).inserted_primary_key[0]

        self.logger.debug(
            f"bot_id={new_channel_post.bot_id}: channel_post_id {channel_post_id} is added",
            extra=extra_params(channel_post_id=channel_post_id,
                               bot_id=new_channel_post.bot_id)
        )

        return channel_post_id

    @validate_call
    async def update_channel_post(self, updated_channel_post: ChannelPostSchema):
        async with self.engine.begin() as conn:
            await conn.execute(
                update(ChannelPost).where(
                    ChannelPost.channel_post_id == updated_channel_post.channel_post_id
                ).values(updated_channel_post.model_dump())
            )

        self.logger.debug(
            f"bot_id={updated_channel_post.bot_id}: channel_post {updated_channel_post.channel_post_id} is updated",
            extra=extra_params(
                channel_post_id=updated_channel_post.channel_post_id, bot_id=updated_channel_post.bot_id)
        )

    @validate_call
    async def delete_channel_post(self, channel_post_id: int) -> None:
        if type(channel_post_id) != int:
            raise InvalidParameterFormat(
                "new_channel_post must be type of int")

        async with self.engine.begin() as conn:
            await conn.execute(
                delete(ChannelPost).where(
                    ChannelPost.channel_post_id == channel_post_id
                )
            )

        self.logger.debug(
            f"channel_post_id={channel_post_id}: channel_post {channel_post_id} is deleted",
            extra=extra_params(channel_post_id=channel_post_id)
        )
