from pydantic import BaseModel, Field, validate_call, ConfigDict

from sqlalchemy import BigInteger, Column, ForeignKey, UniqueConstraint, \
    select, insert, delete, BOOLEAN, update
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot
from database.exceptions.exceptions import KwargsException

from logs.config import extra_params


class ChannelNotFoundError(KwargsException):
    """Raised when provided channel not found in database"""


class Channel(Base):
    __tablename__ = "channels"
    channel_id = Column(BigInteger, primary_key=True, unique=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), nullable=False)

    # import because everyone can add bots. So now let our admins know only about their channels
    added_by_admin = Column(BOOLEAN, nullable=False)

    __table_args__ = (
        UniqueConstraint('channel_id', 'bot_id', name='unique_channel_bot'),
    )


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
        """
        Returns list of ChannelSchema of bot_id
        """
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
        """
        :raises ChannelNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Channel).where(Channel.channel_id == channel_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ChannelNotFoundError(
                channel_id=channel_id
            )

        res = ChannelSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: found channel {res}",
            extra=extra_params(bot_id=res.bot_id, channel_id=channel_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_channel(self, new_channel: ChannelSchema) -> None:
        """
        :raises IntegrityError:
        """
        async with self.engine.begin() as conn:
            await conn.execute(insert(Channel).values(new_channel.model_dump()))

        self.logger.debug(
            f"bot_id={new_channel.bot_id}: added channel {new_channel}",
            extra=extra_params(bot_id=new_channel.bot_id,
                               channel_id=new_channel.channel_id)
        )

    @validate_call(validate_return=True)
    async def update_channel(self, updated_channel: ChannelSchema) -> None:
        """
        Updates Channel in database
        """
        async with self.engine.begin() as conn:
            await conn.execute(update(Channel).where(Channel.channel_id == updated_channel.channel_id).
                               values(**updated_channel.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"channel_id={updated_channel.channel_id}: updated channel {updated_channel}",
            extra=extra_params(channel_id=updated_channel.channel_id, bot_id=updated_channel.bot_id)
        )

    @validate_call(validate_return=True)
    async def delete_channel(self, channel: ChannelSchema) -> None:
        """
        Deletes Channel from database
        """
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(Channel).where(
                    Channel.channel_id == channel.channel_id, Channel.bot_id == channel.bot_id
                )
            )

        self.logger.debug(
            f"bot_id={channel.bot_id}: deleted channel {channel}",
            extra=extra_params(bot_id=channel.bot_id,
                               channel_id=channel.channel_id)
        )
