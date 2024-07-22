from enum import Enum

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import select, update, delete, insert
from sqlalchemy import Column, String, TypeDecorator, Unicode, Dialect, ForeignKey

from pydantic import BaseModel, ConfigDict, Field

from database.models import Base
from database.exceptions import *
from database.models.dao import Dao
from database.models.bot_model import Bot
from database.models.user_model import User

from typing import *

from logs.config import extra_params


class UserRoleValues(Enum):
    OWNER = "owner"
    ADMINISTRATOR = "admin"


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


class UserRole(Base):
    __tablename__ = "user_role"

    user_id = Column(ForeignKey(User.user_id, ondelete="CASCADE"), primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), primary_key=True)
    role = Column(UserRoleEnum, nullable=False)


class UserRoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(frozen=True)
    bot_id: int = Field(frozen=True)
    role: UserRoleValues


class UserRoleDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    async def get_user_role(self, user_id: int, bot_id: int) -> UserRoleSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(UserRole).where(UserRole.user_id == user_id,
                                                                UserRole.bot_id == bot_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise UserRoleNotFound(f"user_id={user_id} bot_id={bot_id} user role not found in database.")

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
        self.logger.debug(
            f"user_id={new_role.user_id} bot_id={new_role.bot_id}: new user role created with role {new_role.role}",
            extra=extra_params(user_id=new_role.user_id, bot_id=new_role.bot_id))

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

