from enum import Enum
from typing import Optional
from datetime import datetime

from sqlalchemy import BigInteger, Column, String, DateTime, JSON, TypeDecorator, Unicode, Dialect, ARRAY, ForeignKey
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict

from database.models import Base
from database.exceptions import *
from database.models.dao import Dao
from database.models.bot_model import Bot

from database.config import bot_db

from logs.config import extra_params


class UserStatusValues(Enum):
    BANNED = "banned"
    NEW = "new"
    TRIAL = "trial"
    SUBSCRIBED = "subscribed"
    SUBSCRIPTION_ENDED = "subscription_ended"


class UserRoleValues(Enum):
    OWNER = "owner"
    ADMINISTRATOR = "admin"


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


class UserRoleEnum(TypeDecorator):  # noqa
    impl = Unicode
    cache_ok = True

    def process_bind_param(self, value: Optional[UserRoleValues], dialect: Dialect) -> String:
        return value.value

    def process_result_value(self, value: Optional[String], dialect: Dialect) -> Optional[UserRoleValues]:
        match value:
            case UserRoleValues.OWNER.value:
                return UserRoleValues.OWNER
            case UserRoleValues.ADMINISTRATOR.value:
                return UserRoleValues.ADMINISTRATOR


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
    subscription_job_ids = Column(ARRAY(String))


class UserRole(Base):
    __tablename__ = "user_role"

    user_id = Column(ForeignKey(User.user_id, ondelete="CASCADE"), primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), primary_key=True)
    role = Column(UserRoleEnum, nullable=False)


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
    subscription_job_ids: list[str] | None = None


class UserRoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(frozen=True)
    bot_id: int = Field(frozen=True)
    role: UserRoleValues


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

    # TODO change auto_create to False after updating all old users
    async def get_user_role(self, user_id: int, bot_id: int, auto_create_new_role: bool = True) -> UserRoleSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(UserRole).where(UserRole.user_id == user_id,
                                                                UserRole.bot_id == bot_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            if not auto_create_new_role:
                raise UserRoleNotFound(f"user_id={user_id} bot_id={bot_id} user role not found in database.")

            self.logger.debug(
                f"user_id={user_id} bot_id={bot_id}: role not found, auto creating new role",
                extra=extra_params(user_id=user_id, bot_id=bot_id))
            bot = await bot_db.get_bot(bot_id)
            if bot.created_by == user_id:
                role = UserRoleValues.OWNER
            else:
                role = UserRoleValues.ADMINISTRATOR
            await self.add_user_role(UserRoleSchema(user_id=user_id, bot_id=bot_id, role=role))
            return await self.get_user_role(user_id, bot_id)

        res = UserRoleSchema.model_validate(res)

        self.logger.debug(
            f"user_id={user_id} bot_id={bot_id}: user role is found",
            extra=extra_params(user_id=user_id, bot_id=bot_id)
        )

        return res

    async def add_user_role(self, new_role: UserRoleSchema) -> None:
        try:
            await self.get_user_role(user_id=new_role.user_id, bot_id=new_role.bot_id)
            raise InstanceAlreadyExists(
                f"user_role with user_id={new_role.user_id} bot_id={new_role.bot_id} already exists in db.")
        except UserRoleNotFound:
            async with self.engine.begin() as conn:
                await conn.execute(insert(UserRole).values(**new_role.model_dump(by_alias=True)))
            await self.engine.dispose()

    async def update_user_role(self, updated_role: UserRoleSchema) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(update(UserRole).where(UserRole.user_id == updated_role.user_id,
                                                      UserRole.bot_id == updated_role.bot_id).
                               values(**updated_role.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={updated_role.user_id} bot_id={updated_role.bot_id}: user role is updated",
            extra=extra_params(user_id=updated_role.user_id, bot_id=updated_role.bot_id)
        )

    async def del_user_role(self, user_id: int, bot_id: int) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(delete(UserRole).where(UserRole.user_id == user_id,
                                                      UserRole.bot_id == bot_id))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={user_id} bot_id={bot_id}: user role is deleted",
            extra=extra_params(user_id=user_id, bot_id=bot_id)
        )
