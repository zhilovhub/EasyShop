from enum import Enum

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import select, update, delete, insert
from sqlalchemy import Column, String, TypeDecorator, Unicode, Dialect, ForeignKey

from pydantic import BaseModel, ConfigDict, Field, validate_call

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot, BotSchema
from database.models.user_model import User
from database.exceptions.exceptions import KwargsException

from typing import *

from logs.config import extra_params


class UserRoleNotFoundError(KwargsException):
    """Raised when provided user's role not found in database"""


class UserRoleValues(Enum):
    OWNER = "owner"
    ADMINISTRATOR = "admin"


class UserRoleEnum(TypeDecorator):  # noqa
    """Class to convert Enum values to db values (and reverse)"""
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

    @validate_call(validate_return=True)
    async def get_user_bots(self, user_id: int) -> list[BotSchema]:
        """
        :raises UserRoleNotFoundError
        """
        # check if user is bot creator and add owner role to bots if it not exists
        async with self.engine.begin() as conn:
            raw_own_bots = await conn.execute(select(Bot).where(Bot.created_by == user_id))
            own_bots = raw_own_bots.fetchall()
            for bot in own_bots:
                try:
                    await self.get_user_role(user_id, bot.bot_id)
                except UserRoleNotFoundError:
                    new_role = UserRoleSchema(user_id=user_id, bot_id=bot.bot_id, role=UserRoleValues.OWNER)
                    await self.add_user_role(new_role)

        # get all user roles
        async with self.engine.begin() as conn:
            raw_data = await conn.execute(select(UserRole).where(UserRole.user_id == user_id))
            raw_data = raw_data.fetchall()
            if raw_data is None:
                raise UserRoleNotFoundError(user_id=user_id)
            data = []
            for user_role in raw_data:
                data.append(UserRoleSchema.model_validate(user_role))

        # get bots by user role objects
        async with self.engine.begin() as conn:
            bots = []
            for user_role in data:
                raw_bot = await conn.execute(select(Bot).where(Bot.bot_id == user_role.bot_id))
                raw_bot = raw_bot.fetchone()
                if raw_bot:
                    bots.append(BotSchema.model_validate(raw_bot))

        self.logger.debug(
            f"user_id={user_id}: has {len(bots)} roles in different bots",
            extra=extra_params(user_id=user_id)
        )

        return bots

    @validate_call(validate_return=True)
    async def get_user_role(self, user_id: int, bot_id: int) -> UserRoleSchema:
        """
        :raises UserRoleNotFoundError
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(UserRole).where(UserRole.user_id == user_id,
                                                                UserRole.bot_id == bot_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise UserRoleNotFoundError(user_id=user_id, bot_id=bot_id)

        res = UserRoleSchema.model_validate(res)

        self.logger.debug(
            f"user_id={user_id} bot_id={bot_id}: found user_role {res}",
            extra=extra_params(user_id=user_id, bot_id=bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_user_role(self, new_role: UserRoleSchema) -> None:
        """
        :raises IntegrityError
        """
        async with self.engine.begin() as conn:
            await conn.execute(insert(UserRole).values(**new_role.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={new_role.user_id} bot_id={new_role.bot_id}: added user_role {new_role}",
            extra=extra_params(user_id=new_role.user_id, bot_id=new_role.bot_id)
        )

    @validate_call(validate_return=True)
    async def update_user_role(self, updated_role: UserRoleSchema) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(update(UserRole).where(UserRole.user_id == updated_role.user_id,
                                                      UserRole.bot_id == updated_role.bot_id).
                               values(**updated_role.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={updated_role.user_id} bot_id={updated_role.bot_id}: updated user_role {updated_role}",
            extra=extra_params(user_id=updated_role.user_id, bot_id=updated_role.bot_id)
        )

    @validate_call(validate_return=True)
    async def del_user_role(self, user_id: int, bot_id: int) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(delete(UserRole).where(UserRole.user_id == user_id,
                                                      UserRole.bot_id == bot_id))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={user_id} bot_id={bot_id}: deleted user_role",
            extra=extra_params(user_id=user_id, bot_id=bot_id)
        )

    @validate_call(validate_return=True)
    async def get_bot_admin_ids(self, bot_id: int) -> list[int]:
        """
        Returns all user ids who has ADMINISTRATOR role in bot
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(UserRole).where(UserRole.bot_id == bot_id,
                                                                UserRole.role == UserRoleValues.ADMINISTRATOR))
        await self.engine.dispose()

        res = raw_res.fetchall()

        if res is None:
            return []

        ids = []
        for admin in res:
            admin_obj = UserRoleSchema.model_validate(admin)
            ids.append(admin_obj.user_id)

        return ids
