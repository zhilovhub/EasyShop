from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from datetime import datetime

from sqlalchemy import BOOLEAN, BigInteger, Column, String, DateTime, JSON, TypeDecorator, Unicode, Dialect
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict

from database.models import Base
from database.models.dao import Dao
from sqlalchemy import ForeignKey
from bot.exceptions.exceptions import *
from logs.config import extra_params
from database.models.channel_model import Channel
from database.models.channel_post_model import ChannelPost


class ContestUserNotFound(Exception):
    pass


class ContestUser(Base):
    __tablename__ = "contest_users"
    channel_user_pk = Column(BigInteger, primary_key=True, autoincrement=True)
    contest_post_id = Column(ForeignKey(
        ChannelPost.channel_post_id), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    channel_id = Column(ForeignKey(Channel.channel_id,
                        ondelete="CASCADE"), nullable=False)
    join_date = Column(DateTime, nullable=False)


class ContestUserSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contest_post_id: int = Field(frozen=True)
    user_id: int = Field(frozen=True)
    channel_id: int = Field(frozen=True)
    join_date: datetime = Field()


class ContestUserSchema(ContestUserSchemaWithoutId):
    channel_user_pk: int = Field(frozen=True)


class ContestUserDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    async def get_contest_users_by_contest_id(self, contest_id: int) -> list[ContestUserSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ContestUser).where(
                    ContestUser.contest_post_id == contest_id
                )
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for contest_user in raw_res:
            res.append(ContestUserSchema.model_validate(contest_user))

        self.logger.debug(
            f"There are {len(res)} contest users in {contest_id} contest"
        )
        return res

    async def get_contest_user_by_contest_id_and_user_id(self, contest_id: int, user_id: int) -> ContestUserSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ContestUser).where(
                    ContestUser.contest_post_id == contest_id,
                    ContestUser.user_id == user_id,
                )
            )
        await self.engine.dispose()
        res = raw_res.fetchone()
        if res is None:
            raise ContestUserNotFound(
                f"id {user_id} not found in {contest_id} contest.")

        res = ContestUserSchema.model_validate(res)

        self.logger.debug(
            f"user_id={user_id} in contest {contest_id} is found",
            extra=extra_params(user_id=user_id, contest_id=contest_id)
        )

        return res

    async def add_contest_user(self, contest_user: ContestUserSchemaWithoutId) -> None:
        if not isinstance(contest_user, ContestUserSchemaWithoutId):
            raise InvalidParameterFormat(
                "contest_user must be type of ContestUserSchemaWithoutId.")

        try:
            await self.get_contest_user_by_contest_id_and_user_id(
                contest_id=contest_user.contest_post_id, user_id=contest_user.user_id
            )
            raise InstanceAlreadyExists(
                f"ContestUser with {contest_user.user_id} already exists in contest {contest_user.contest_post_id}.")
        except ContestUserNotFound:
            async with self.engine.begin() as conn:
                await conn.execute(insert(ContestUser).values(**contest_user.model_dump(by_alias=True)))
            await self.engine.dispose()

        self.logger.debug(
            f"contest_user_id={contest_user.user_id}: ContestUser {contest_user.channel_id} is added",
            # extra=extra_params()
        )

    # async def del_channel_user(self, channel_user_id: int) -> None:
    #     if not isinstance(channel_user_id, int):
    #         raise InvalidParameterFormat(
    #             "channel_user_id must be type of int.")

    #     async with self.engine.begin() as conn:
    #         await conn.execute(delete(ChannelUser).where(ChannelUser.channel_user_id == channel_user_id))
    #     await self.engine.dispose()

    #     self.logger.debug(
    #         f"channel_user_id={channel_user_id}: ChannelUser {channel_user_id} is deleted",
    #         extra=extra_params(channel_user_id=channel_user_id)
    #     )
