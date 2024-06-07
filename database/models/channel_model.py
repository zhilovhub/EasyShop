from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.bot_model import Bot
from database.models.dao import Dao
from logs.config import extra_params


class ChannelNotFound(Exception):
    """Raised when provided channel not found in database"""
    pass


class Channel(Base):
    __tablename__ = "channels"

    channel_id = Column(BigInteger, primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), primary_key=True)

    # import because everyone can add bots. So now let our admins know only about their channels
    added_by_admin = Column(BOOLEAN, nullable=False)


class ChannelSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: int = Field(frozen=True)
    bot_id: int = Field(frozen=True)

    added_by_admin: bool


class ChannelDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_channels(self, bot_id: int) -> list[ChannelSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Channel).where(Channel.bot_id == bot_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for channel in raw_res:
            res.append(ChannelSchema.model_validate(channel))

        self.logger.debug(
            f"bot_id={bot_id}: has {len(res)} channels",
            extra=extra_params(bot_id=bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_channel(self, channel_id: int) -> ChannelSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Channel).where(Channel.id == channel_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ChannelNotFound

        res = ChannelSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: channel {channel_id} is found",
            extra=extra_params(bot_id=res.bot_id, channel_id=channel_id)
        )

        return res

    @validate_call
    async def add_channel(self, new_channel: ChannelSchema) -> None:
        if type(new_channel) != ChannelSchema:
            raise InvalidParameterFormat("new_channel must be type of ChannelSchema")

        async with self.engine.begin() as conn:
            await conn.execute(insert(Channel).values(new_channel.model_dump()))

        self.logger.debug(
            f"bot_id={new_channel.bot_id}: channel {new_channel.channel_id} is added",
            extra=extra_params(bot_id=new_channel.bot_id, channel_id=new_channel.channel_id)
        )

    @validate_call
    async def delete_channel(self, new_channel: ChannelSchema) -> None:
        if type(new_channel) != ChannelSchema:
            raise InvalidParameterFormat("new_channel must be type of ChannelSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                delete(Channel).where(
                    Channel.channel_id == new_channel.channel_id, Channel.bot_id == new_channel.bot_id
                )
            )

        self.logger.debug(
            f"bot_id={new_channel.bot_id}: channel {new_channel.channel_id} is deleted",
            extra=extra_params(bot_id=new_channel.bot_id, channel_id=new_channel.channel_id)
        )
