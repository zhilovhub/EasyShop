from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, UniqueConstraint, select, insert, delete, BOOLEAN
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions.exceptions import InstanceAlreadyExists
from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.bot_model import Bot
from database.models.dao import Dao
from logs.config import extra_params
from database.models.channel_post_model import ChannelPost


class ContestChannelNotFound(Exception):
    """Raised when provided channel not found in database"""
    pass


class ContestChannel(Base):
    __tablename__ = "contest_channels"
    contest_channel_pk = Column(
        BigInteger, primary_key=True, autoincrement=True)
    channel_id = Column(BigInteger, unique=True, nullable=False)
    contest_post_id = Column(ForeignKey(
        ChannelPost.channel_post_id, ondelete="CASCADE"), nullable=False)


class ContestChannelSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: int = Field(frozen=True)
    contest_post_id: int = Field(frozen=True)


class ContestChannelSchema(ContestChannelSchemaWithoutId):
    contest_channel_pk: int = Field(frozen=True)


class ContestChannelDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_contest_channels_by_contest_post_id(self, contest_id: int) -> list[ContestChannelSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ContestChannel).where(
                    ContestChannel.contest_post_id == contest_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for channel in raw_res:
            res.append(ContestChannelSchema.model_validate(channel))

        self.logger.debug(
            f"contest with id ={contest_id}: has {len(res)} channels",
        )

        return res

    async def get_contest_channel_by_channel_id_and_contest_id(self, contest_id, channel_id) -> ContestChannelSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ContestChannel).where(
                    ContestChannel.channel_id == channel_id,
                    ContestChannel.contest_post_id == contest_id,
                )
            )
        await self.engine.dispose()
        res = raw_res.fetchone()
        if res is None:
            raise ContestChannelNotFound(
                f"id {channel_id} not found in {contest_id} contest.")

        res = ContestChannelSchema.model_validate(res)

        self.logger.debug(
            f"channel_id={channel_id} in contest {contest_id} is found",
            extra=extra_params(channel_id=channel_id, contest_id=contest_id)
        )

        return res

    @validate_call
    async def add_channel(self, new_channel: ContestChannelSchemaWithoutId) -> None:
        if type(new_channel) != ContestChannelSchemaWithoutId:
            raise InvalidParameterFormat(
                "new_channel must be type of ContestChannelSchemaWithoutId")
        try:
            await self.get_contest_channel_by_channel_id_and_contest_id(new_channel.contest_post_id, new_channel.channel_id)
            raise InstanceAlreadyExists(
                f"ContestChannel with {new_channel.channel_id} already exists in contest {new_channel.contest_post_id}.")
        except ContestChannelNotFound:

            async with self.engine.begin() as conn:
                contest_channel_pk = (await conn.execute(insert(ContestChannel).values(new_channel.model_dump()))).inserted_primary_key[0]

            self.logger.debug(
                f"contest_id={new_channel.contest_post_id}: channel {new_channel.channel_id} is added",
                extra=extra_params(contest_id=new_channel.contest_post_id,
                                   channel_id=new_channel.channel_id)
            )
        return contest_channel_pk

    @validate_call
    async def delete_channels_by_contest_id(self, contest_id: int) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(ContestChannel).where(
                    ContestChannel.contest_post_id == contest_id
                )
            )

        self.logger.debug(
            f"contest_id={contest_id}: channels are deleted",
            # extra=extra_params(contest_id=new_channel.contest_post_id,
            #                    channel_id=new_channel.channel_id)
        )

    @validate_call
    async def delete_channel(self, new_channel: ContestChannelSchema) -> None:
        if type(new_channel) != ContestChannelSchema:
            raise InvalidParameterFormat(
                "new_channel must be type of ContestChannelSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                delete(ContestChannel).where(
                    ContestChannel.channel_id == new_channel.channel_id
                )
            )

        self.logger.debug(
            f"contest_id={new_channel.contest_post_id}: channel {new_channel.channel_id} is deleted",
            extra=extra_params(contest_id=new_channel.contest_post_id,
                               channel_id=new_channel.channel_id)
        )
