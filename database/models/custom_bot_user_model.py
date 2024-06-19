from sqlalchemy import BigInteger, Column, String, ForeignKey, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict

from bot.exceptions import InvalidParameterFormat, InstanceAlreadyExists
from database.models import Base
from database.models.bot_model import Bot
from database.models.dao import Dao
from logs.config import extra_params


class CustomBotUserNotFound(Exception):
    """Raised when provided custom user not found in database"""
    pass


class CustomBotUser(Base):
    __tablename__ = "custom_bot_users"

    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    balance = Column(BigInteger, default=0)


class CustomBotUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int
    user_id: int
    balance: int | None = 0


class CustomBotUserDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    async def get_custom_bot_user(self, bot_id: int, user_id: int) -> CustomBotUserSchema:  # TODO write tests
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(CustomBotUser).where(
                CustomBotUser.bot_id == bot_id, CustomBotUser.user_id == user_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise CustomBotUserNotFound(f"user with user_id = {user_id} of bot_id = {bot_id} not found in database")

        res = CustomBotUserSchema.model_validate(res)

        self.logger.debug(
            f"bot_id={bot_id}: user {user_id} is found",
            extra=extra_params(user_id=user_id, bot_id=bot_id)
        )

        return res

    async def get_custom_bot_users(self, bot_id: int) -> list[CustomBotUserSchema]:  # TODO write tests
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(CustomBotUser).where(CustomBotUser.bot_id == bot_id))
        await self.engine.dispose()

        users = []
        for raw in raw_res.fetchall():
            users.append(
                CustomBotUserSchema.model_validate(raw)
            )

        self.logger.debug(
            f"bot_id={bot_id}: has {len(users)} users",
            extra=extra_params(bot_id=bot_id)
        )

        return users

    async def update_custom_bot_user(self, updated_user: CustomBotUserSchema):
        async with self.engine.begin() as conn:
            await conn.execute(update(CustomBotUser).where(CustomBotUser.user_id == updated_user.user_id).
                               values(**updated_user.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={updated_user.user_id}, bot_id={updated_user.bot_id}: "
            f"custom bot user {updated_user.user_id} is updated",
            extra=extra_params(user_id=updated_user.user_id, bot_id=updated_user.bot_id)
        )

    async def add_custom_bot_user(self, bot_id: int, user_id: int) -> None:  # TODO write tests
        if type(bot_id) != int or type(user_id) != int:
            raise InvalidParameterFormat("user_id and bot_id must be type of int")

        async with self.engine.begin() as conn:
            try:
                await conn.execute(insert(CustomBotUser).values(bot_id=bot_id, user_id=user_id))
            except IntegrityError:
                raise InstanceAlreadyExists(f"user_id {user_id} of bot_id {bot_id} already exists in db or bot_id with "
                                            f"bot_id = {bot_id} does not exist")
        await self.engine.dispose()

        self.logger.debug(
            f"bot_id={bot_id}: user {user_id} is added",
            extra=extra_params(user_id=user_id, bot_id=bot_id)
        )
