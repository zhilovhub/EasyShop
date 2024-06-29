from datetime import datetime
from datetime import timedelta

from pydantic import BaseModel, Field, ConfigDict

from sqlalchemy import ForeignKey, BOOLEAN, BigInteger, Column, DateTime, select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions.exceptions import *

from database.models import Base
from database.models.dao import Dao
from database.models.channel_model import Channel

from logs.config import extra_params


class ChannelUser(Base):
    __tablename__ = "channel_users"
    channel_user_pk = Column(BigInteger, primary_key=True, autoincrement=True)
    channel_user_id = Column(BigInteger, nullable=False)
    channel_id = Column(ForeignKey(Channel.channel_id,
                        ondelete="CASCADE"), nullable=False)
    is_channel_member = Column(BOOLEAN, nullable=True)
    join_date = Column(DateTime, nullable=False)


class ChannelUserSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_user_id: int = Field(frozen=True)
    channel_id: int = Field(frozen=True)
    is_channel_member: bool = None
    join_date: datetime = Field()


class ChannelUserSchema(ChannelUserSchemaWithoutId):
    channel_user_pk: int = Field(frozen=True)


class ChannelUserDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    async def get_joined_channel_users_by_channel_id(self, channel_id: int) -> list[ChannelUserSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ChannelUser).where(
                    (ChannelUser.channel_id == channel_id),
                    ((datetime.now() - ChannelUser.join_date) < timedelta(hours=24)),
                    (ChannelUser.is_channel_member is True)
                )
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for channel_user in raw_res:
            res.append(ChannelUserSchema.model_validate(channel_user))

        self.logger.debug(
            f"There are {len(res)} ChannelUsers in our service"
        )
        return res

    async def get_left_channel_users_by_channel_id(self, channel_id: int) -> list[ChannelUserSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ChannelUser).where(
                    (ChannelUser.channel_id == channel_id),
                    ((datetime.now() - ChannelUser.join_date) < timedelta(hours=24)),
                    (ChannelUser.is_channel_member is False)
                )
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for channel_user in raw_res:
            res.append(ChannelUserSchema.model_validate(channel_user))

        self.logger.debug(
            f"There are {len(res)} ChannelUsers in our service"
        )
        return res

    async def get_channel_users(self) -> list[ChannelUserSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(ChannelUser))
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for channel_user in raw_res:
            res.append(ChannelUserSchema.model_validate(channel_user))

        self.logger.debug(
            f"There are {len(res)} ChannelUsers in our service"
        )

        return res

    async def get_channel_user_by_channel_user_id_and_channel_id(
            self,
            channel_user_id: int,
            channel_id: int
    ) -> ChannelUserSchema:
        if not isinstance(channel_user_id, int):
            raise InvalidParameterFormat("ChannelUser_id must be type of int.")

        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ChannelUser).where(
                    (ChannelUser.channel_user_id == channel_user_id),
                    (ChannelUser.channel_id == channel_id)
                )
            )
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise ChannelUserNotFound(
                f"id {channel_user_id} not found in database.")

        res = ChannelUserSchema.model_validate(res)

        self.logger.debug(
            f"channel_user_id={channel_user_id}: ChannelUser {channel_user_id} is found",
            extra=extra_params(channel_user_id=channel_user_id)
        )

        return res

    async def add_channel_user(self, channel_user: ChannelUserSchemaWithoutId) -> None:
        if not isinstance(channel_user, ChannelUserSchemaWithoutId):
            raise InvalidParameterFormat(
                "ChannelUser must be type of database.DbChannelUser.")

        try:
            await self.get_channel_user_by_channel_user_id_and_channel_id(
                channel_user_id=channel_user.channel_user_id, channel_id=channel_user.channel_id
            )
            raise InstanceAlreadyExists(
                f"ChannelUser with {channel_user.channel_user_id} already exists in db.")
        except ChannelUserNotFound:
            async with self.engine.begin() as conn:
                await conn.execute(insert(ChannelUser).values(**channel_user.model_dump(by_alias=True)))
            await self.engine.dispose()

        self.logger.debug(
            f"channel_user_id={channel_user.channel_user_id}: ChannelUser {channel_user.channel_user_id} is added",
            extra=extra_params(channel_user_id=channel_user.channel_user_id)
        )

    async def update_channel_user(self, updated_channel_user: ChannelUserSchema) -> None:
        if not isinstance(updated_channel_user, ChannelUserSchema):
            raise InvalidParameterFormat(
                "updated_ChannelUser must be type of database.DbChannelUser.")

        async with self.engine.begin() as conn:
            await conn.execute(
                update(ChannelUser).where(
                    ChannelUser.channel_user_id == updated_channel_user.channel_user_id
                ).values(**updated_channel_user.model_dump(by_alias=True))
            )
        await self.engine.dispose()

        self.logger.debug(
            f"channel_user_id={updated_channel_user.channel_user_id}: "
            f"ChannelUser {updated_channel_user.channel_user_id} is updated",
            extra=extra_params(
                channel_user_id=updated_channel_user.channel_user_id
            )
        )

    async def del_channel_user(self, channel_user_id: int) -> None:
        if not isinstance(channel_user_id, int):
            raise InvalidParameterFormat(
                "channel_user_id must be type of int.")

        async with self.engine.begin() as conn:
            await conn.execute(delete(ChannelUser).where(ChannelUser.channel_user_id == channel_user_id))
        await self.engine.dispose()

        self.logger.debug(
            f"channel_user_id={channel_user_id}: ChannelUser {channel_user_id} is deleted",
            extra=extra_params(channel_user_id=channel_user_id)
        )
