from enum import Enum
from typing import Optional
from datetime import datetime

from sqlalchemy import BigInteger, Column, String, DateTime, JSON, TypeDecorator, Unicode, Dialect, ARRAY
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict, validate_call

from database.models import Base
from database.models.dao import Dao
from database.exceptions.exceptions import KwargsException

from logs.config import extra_params


class UserNotFoundError(KwargsException):
    """Raised when provided user not found in database"""


class UnknownUserStatus(KwargsException):
    """Raised when provided user status is not expected"""


class UserStatusValues(Enum):
    BANNED = "banned"
    NEW = "new"
    TRIAL = "trial"
    SUBSCRIBED = "subscribed"
    SUBSCRIPTION_ENDED = "subscription_ended"


class UserStatus(TypeDecorator):  # noqa
    """Class to convert Enum values to db values (and reverse)"""
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


class NotInUserStatusesListError(ValueError):
    """Error when value of user status not in values list"""


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


class UserDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_user(self, user_id: int) -> UserSchema:
        """
        :raises UserNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(User).where(User.user_id == user_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise UserNotFoundError(user_id=user_id)

        res = UserSchema.model_validate(res)

        self.logger.debug(
            f"user_id={user_id}: user {user_id} is found",
            extra=extra_params(user_id=user_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_user(self, user: UserSchema) -> None:
        """
        :raises IntegrityError:
        """
        async with self.engine.begin() as conn:
            await conn.execute(insert(User).values(**user.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={user.id}: added user {user}",
            extra=extra_params(user_id=user.id)
        )

    @validate_call(validate_return=True)
    async def update_user(self, updated_user: UserSchema) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(update(User).where(User.user_id == updated_user.id).
                               values(**updated_user.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={updated_user.id}: updated user {updated_user}",
            extra=extra_params(user_id=updated_user.id)
        )

    @validate_call(validate_return=True)
    async def del_user(self, user_id: int) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(delete(User).where(User.user_id == user_id))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={user_id}: deleted user {user_id}",
            extra=extra_params(user_id=user_id)
        )
