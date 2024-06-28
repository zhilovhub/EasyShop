from datetime import datetime

from pydantic import BaseModel, Field, validate_call, ConfigDict

from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, DateTime
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions.exceptions import InstanceAlreadyExists, InvalidParameterFormat

from database.models import Base
from database.models.dao import Dao
from database.models.post_message_model import PostMessage

from logs.config import extra_params


class ChannelContestNotFound(Exception):
    """Raised when provided contest not found in database"""
    pass


class ChannelContest(Base):
    __tablename__ = "channel_contest"
    contest_id = Column(BigInteger, primary_key=True, autoincrement=True)

    channel_id = Column(BigInteger, unique=True, nullable=False)
    post_message_id = Column(ForeignKey(PostMessage.post_message_id, ondelete="CASCADE"), nullable=False)

    contest_end_date = Column(DateTime, nullable=True)
    contest_winner_amount = Column(BigInteger, nullable=True)


class ContestChannelSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: int = Field(frozen=True)
    post_message_id: int = Field(frozen=True)

    contest_end_date: datetime | None = None
    contest_winner_amount: int | None = None


class ChannelContestSchema(ContestChannelSchemaWithoutId):
    contest_id: int = Field(frozen=True)


class ChannelContestDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_channel_contest(self, channel_id: int) -> ChannelContestSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ChannelContest).where(
                    ChannelContest.channel_id == channel_id,
                )
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ChannelContestNotFound

        res = ChannelContestSchema.model_validate(raw_res)

        self.logger.debug(
            f"channel_id={res.channel_id}: contest_id={res.contest_id} is found: {res}",
            extra=extra_params(channel_id=channel_id, contest_id=res.contest_id)
        )

        return res

    @validate_call
    async def add_channel_contest(self, new_channel_contest: ContestChannelSchemaWithoutId) -> int:
        if type(new_channel_contest) != ContestChannelSchemaWithoutId:
            raise InvalidParameterFormat(
                "new_channel_contest must be type of ContestChannelSchemaWithoutId")
        try:
            await self.get_channel_contest(new_channel_contest.channel_id)
            raise InstanceAlreadyExists(
                f"channel_id={new_channel_contest.channel_id} already have channel_contest"
            )
        except ChannelContestNotFound:
            async with self.engine.begin() as conn:
                channel_contest_id = (
                    await conn.execute(insert(ChannelContest).values(new_channel_contest.model_dump()))
                ).inserted_primary_key[0]

            self.logger.debug(
                f"channel_id={new_channel_contest.channel_id}: "
                f"contest_id={channel_contest_id} is added: {new_channel_contest} ",
                extra=extra_params(
                    contest_id=channel_contest_id,
                    channel_id=new_channel_contest.channel_id
                )
            )
        return channel_contest_id

    @validate_call
    async def delete_contest(self, channel_contest: ChannelContestSchema) -> None:
        if type(channel_contest) != ChannelContestSchema:
            raise InvalidParameterFormat("new_channel_contest must be type of ChannelContestSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                delete(ChannelContestSchema).where(
                    ChannelContestSchema.channel_id == channel_contest.channel_id
                )
            )

        self.logger.debug(
            f"channel_id={channel_contest.channel_id}: contest {channel_contest.contest_id} is deleted",
            extra=extra_params(contest_id=channel_contest.contest_id, channel_id=channel_contest.channel_id)
        )
