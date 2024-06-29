from enum import Enum
from typing import Optional
from datetime import datetime

from sqlalchemy import BigInteger, Column, String, DateTime, JSON, TypeDecorator, Unicode, Dialect
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict

from bot.exceptions.exceptions import *

from database.models import Base
from database.models.dao import Dao

from logs.config import extra_params


class UserStatusValues(Enum):
    BANNED = "banned"
    NEW = "new"
    TRIAL = "trial"
    SUBSCRIBED = "subscribed"
    SUBSCRIPTION_ENDED = "subscription_ended"


class UserStatus(TypeDecorator):  # noqa
    impl = Unicode
    cache_ok = True

    def process_bind_param(self, value: Optional[UserStatusValues], dialect: Dialect) -> String:
        return value.value

    def process_result_value(self, value: Optional[String], dialect: Dialect) -> Optional[UserStatusValues]:
        match value:
            case UserStatusValues.BANNED.value:
                return UserStatusValues.BANNED
            case UserStatusValues.NEW.value:
                return UserStatusValues.NEW
            case UserStatusValues.TRIAL.value:
                return UserStatusValues.TRIAL
            case UserStatusValues.SUBSCRIBED.value:
                return UserStatusValues.SUBSCRIBED
            case UserStatusValues.SUBSCRIPTION_ENDED.value:
                return UserStatusValues.SUBSCRIPTION_ENDED


class NotInUserStatusesList(ValueError):
    """Error when value of user status not in values list"""
    pass


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    status = Column(UserStatus, nullable=False)
    subscribed_until = Column(DateTime)
    registered_at = Column(DateTime, nullable=False)
    settings = Column(JSON)
    locale = Column(String(10), nullable=False)
    balance = Column(BigInteger, default=0)


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(alias="user_id", frozen=True)
    username: str | None = None
    status: UserStatusValues
    subscribed_until: datetime | None
    registered_at: datetime = Field(frozen=True)
    settings: dict | None = None
    locale: str = Field(max_length=10, default="default")
    balance: int | None = 0


class UserDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    async def get_users(self) -> list[UserSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(User))
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for user in raw_res:
            res.append(UserSchema.model_validate(user))

        self.logger.debug(
            f"There are {len(res)} users in our service"
        )

        return res

    async def get_user(self, user_id: int) -> UserSchema:
        if not isinstance(user_id, int):
            raise InvalidParameterFormat("user_id must be type of int.")

        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(User).where(User.user_id == user_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise UserNotFound(f"id {user_id} not found in database.")

        res = UserSchema.model_validate(res)

        self.logger.debug(
            f"user_id={user_id}: user {user_id} is found",
            extra=extra_params(user_id=user_id)
        )

        return res

    async def add_user(self, user: UserSchema) -> None:
        if not isinstance(user, UserSchema):
            raise InvalidParameterFormat(
                "user must be type of database.DbUser.")

        try:
            await self.get_user(user_id=user.id)
            raise InstanceAlreadyExists(
                f"user with {user.id} already exists in db.")
        except UserNotFound:
            async with self.engine.begin() as conn:
                await conn.execute(insert(User).values(**user.model_dump(by_alias=True)))
            await self.engine.dispose()

        self.logger.debug(
            f"user_id={user.id}: user {user.id} is added",
            extra=extra_params(user_id=user.id)
        )

    async def update_user(self, updated_user: UserSchema) -> None:
        if not isinstance(updated_user, UserSchema):
            raise InvalidParameterFormat(
                "updated_user must be type of database.DbUser.")

        async with self.engine.begin() as conn:
            await conn.execute(update(User).where(User.user_id == updated_user.id).
                               values(**updated_user.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={updated_user.id}: user {updated_user.id} is updated",
            extra=extra_params(user_id=updated_user.id)
        )

    async def del_user(self, user_id: int) -> None:
        if not isinstance(user_id, int):
            raise InvalidParameterFormat("user_id must be type of int.")

        async with self.engine.begin() as conn:
            await conn.execute(delete(User).where(User.user_id == user_id))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={user_id}: user {user_id} is deleted",
            extra=extra_params(user_id=user_id)
        )
