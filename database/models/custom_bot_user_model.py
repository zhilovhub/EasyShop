from sqlalchemy import BigInteger, Column, String, ForeignKey, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict

from bot.exceptions import InvalidParameterFormat, InstanceAlreadyExists
from database.models import Base
from database.models.bot_model import Bot
from database.models.dao import Dao


class CustomBotUserNotFound(Exception):
    """Raised when provided custom user not found in database"""
    pass


class CustomBotUser(Base):
    __tablename__ = "custom_bot_users"

    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)


class CustomBotUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int
    user_id: int


class CustomBotUserDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    async def get_custom_bot_user(self, bot_id: int, user_id: int) -> int:  # TODO write tests
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(CustomBotUser).where(
                CustomBotUser.bot_id == bot_id, CustomBotUser.user_id == user_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise CustomBotUserNotFound(f"user with user_id = {user_id} of bot_id = {bot_id} not found in database")

        self.logger.info(f"get_custom_bot_user method for bot_id {bot_id} and user_id {user_id} success")

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
        self.logger.info(f"get_custom_bot_users method for bot_id {bot_id} success")

        return users

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

        self.logger.info(f"successfully add custom_user with bot_id {bot_id} and user_id {user_id} to db")
