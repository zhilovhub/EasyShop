from datetime import datetime

from aiogram.utils.token import validate_token, TokenValidationError

from sqlalchemy import BigInteger, Column, String, DateTime, JSON
from sqlalchemy import select, update, delete, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict

from database.models import Base
from database.models.dao import Dao

from bot.exceptions.exceptions import *


class Bot(Base):
    __tablename__ = "bots"

    bot_id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_token = Column(String(46), unique=True)
    status = Column(String(55), nullable=False)
    created_at = Column(DateTime, nullable=False)
    created_by = Column(BigInteger, nullable=False)
    settings = Column(JSON)
    locale = Column(String(10), nullable=False)


class BotSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    token: str = Field(alias="bot_token", frozen=True, max_length=46, min_length=46)
    status: str = Field(max_length=55)
    created_at: datetime = Field(frozen=True)
    created_by: int = Field(frozen=True)
    settings: dict | None = None
    locale: str = Field()


class BotSchema(BotSchemaWithoutId):
    bot_id: int = Field(frozen=True)


class BotDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    async def get_bots(self, user_id: int | None = None) -> list[BotSchema]:
        async with self.engine.begin() as conn:
            if user_id:
                raw_res = await conn.execute(select(Bot).where(Bot.created_by == user_id))
            else:
                raw_res = await conn.execute(select(Bot))
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for bot in raw_res:
            res.append(BotSchema.model_validate(bot))
        self.logger.info(f"get_bots method for user {user_id} success.")
        return res

    async def get_bot(self, bot_id: int) -> BotSchema:
        if not isinstance(bot_id, int):
            raise InvalidParameterFormat(
                "bot_id must be type of int")

        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Bot).where(Bot.bot_id == bot_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise BotNotFound(f"bot with bot_id = {bot_id} not found in database.")

        return BotSchema.model_validate(res)

    async def get_bot_by_token(self, bot_token: str) -> BotSchema:
        try:
            validate_token(bot_token)
        except TokenValidationError:
            raise InvalidParameterFormat(
                "bot_token must be type of str with format 0000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA")

        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Bot).where(Bot.bot_token == bot_token))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise BotNotFound(f"bot with bot_token = {bot_token} not found in database")

        self.logger.info(f"get_bot method token: {bot_token} success.")
        return BotSchema.model_validate(res)

    async def add_bot(self, bot: BotSchemaWithoutId) -> int:
        if not isinstance(bot, BotSchemaWithoutId):
            raise InvalidParameterFormat("bot must be type of BotSchemaWithoutId")

        async with self.engine.begin() as conn:
            try:
                bot_id = (await conn.execute(insert(Bot).values(**bot.model_dump(by_alias=True)))).inserted_primary_key[0]
            except IntegrityError:
                raise InstanceAlreadyExists(f"bot with {bot.token} already exists in db.")
        await self.engine.dispose()

        self.logger.info(f"successfully add bot with bot_id {bot_id} to db.")
        return bot_id

    async def update_bot(self, updated_bot: BotSchema) -> None:
        if not isinstance(updated_bot, BotSchema):
            raise InvalidParameterFormat("updated_user must be type of BotSchema")

        async with self.engine.begin() as conn:
            await conn.execute(update(Bot).where(Bot.bot_id == updated_bot.bot_id).
                               values(**updated_bot.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.info(f"successfully update bot with token {updated_bot.token} in db.")

    async def del_bot(self, bot_id: str) -> None:
        if not isinstance(bot_id, int):
            raise InvalidParameterFormat(
                "bot_id must be type of int")

        async with self.engine.begin() as conn:
            await conn.execute(delete(Bot).where(Bot.bot_id == bot_id))
        await self.engine.dispose()

        self.logger.info(f"successfully delete bot with bot_id = {bot_id} from db")

