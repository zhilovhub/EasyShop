from datetime import datetime

from aiogram.utils.token import validate_token, TokenValidationError

from sqlalchemy import BigInteger, Column, String, DateTime, JSON, ForeignKey
from sqlalchemy import select, update, delete, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict

from database.models import Base
from database.models.dao import Dao

from bot.exceptions.exceptions import *
from database.models.user_model import User
from logs.config import extra_params


class Bot(Base):
    __tablename__ = "bots"

    bot_id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_token = Column(String(46), unique=True)
    status = Column(String(55), nullable=False)
    created_at = Column(DateTime, nullable=False)
    created_by = Column(ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False)
    settings = Column(JSON)
    locale = Column(String(10), nullable=False)


class BotSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

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

        self.logger.debug(
            f"user_id={user_id}: has {len(res)} bots",
            extra=extra_params(user_id=user_id)
        )

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
            raise BotNotFound(f"bot_id={bot_id}: not found in database.")

        self.logger.debug(
            f"bot_id={bot_id}: bot {bot_id} is found",
            extra=extra_params(bot_id=bot_id)
        )

        return BotSchema.model_validate(res)

    async def get_bot_by_created_by(self, created_by: int) -> BotSchema:
        if not isinstance(created_by, int):
            raise InvalidParameterFormat(
                "created_by must be type of int")

        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Bot).where(Bot.created_by == created_by))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise BotNotFound(f"bot with created_by={created_by} not found in database")

        res = BotSchema.model_validate(res)

        self.logger.debug(
            f"bot_id={res.bot_id}: bot with created_by={created_by} is found",
            extra=extra_params(bot_id=res.bot_id, user_id=created_by)
        )

        return res

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

        res = BotSchema.model_validate(res)

        self.logger.debug(
            f"bot_id={res.bot_id}: bot with bot_token={bot_token} is found",
            extra=extra_params(bot_id=res.bot_id, bot_token=bot_token)
        )

        return res

    async def add_bot(self, bot: BotSchemaWithoutId) -> int:
        if type(bot) != BotSchemaWithoutId:
            raise InvalidParameterFormat("bot must be type of BotSchemaWithoutId")

        async with self.engine.begin() as conn:
            try:
                bot_id = (await conn.execute(insert(Bot).values(**bot.model_dump(by_alias=True)))).inserted_primary_key[0]
            except IntegrityError:
                raise InstanceAlreadyExists(f"bot with {bot.token} already exists in db or user with "
                                            f"user_id = {bot.created_by} not exists")
        await self.engine.dispose()

        self.logger.debug(
            f"bot_id={bot_id}: bot {bot_id} is added to",
            extra=extra_params(user_id=bot.created_by, bot_id=bot_id)
        )

        return bot_id

    async def update_bot(self, updated_bot: BotSchema) -> None:
        if not isinstance(updated_bot, BotSchema):
            raise InvalidParameterFormat("updated_user must be type of BotSchema")

        async with self.engine.begin() as conn:
            await conn.execute(update(Bot).where(Bot.bot_id == updated_bot.bot_id).
                               values(**updated_bot.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"bot_id={updated_bot.bot_id}: bot {updated_bot.bot_id} is updated",
            extra=extra_params(user_id=updated_bot.created_by, bot_id=updated_bot.bot_id)
        )

    async def del_bot(self, bot_id: int) -> None:
        if not isinstance(bot_id, int):
            raise InvalidParameterFormat(
                "bot_id must be type of int")

        async with self.engine.begin() as conn:
            await conn.execute(delete(Bot).where(Bot.bot_id == bot_id))
        await self.engine.dispose()

        self.logger.debug(
            f"bot_id={bot_id}: bot {bot_id} is deleted",
            extra=extra_params(bot_id=bot_id)
        )
