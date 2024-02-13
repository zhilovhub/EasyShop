from datetime import datetime
from re import fullmatch

from sqlalchemy import BigInteger, Column, String, DateTime, JSON
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict

from database.models import Base
from database.models.dao import Dao

from bot.config import logger
from bot.exceptions.exceptions import *


class Bot(Base):
    __tablename__ = "bots"

    bot_token = Column(String(46), primary_key=True)
    status = Column(String(55), nullable=False)
    created_at = Column(DateTime, nullable=False)
    created_by = Column(BigInteger, nullable=False)
    settings = Column(JSON)
    locale = Column(String(10), nullable=False)


class BotSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    token: str = Field(alias="bot_token", frozen=True, max_length=46, min_length=46)
    status: str = Field(max_length=55)
    created_at: datetime = Field(frozen=True)
    created_by: int = Field(frozen=True)
    settings: dict | None = None
    locale: str = Field()


class BotDao(Dao):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)

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

        return res

    async def get_bot(self, bot_token: str) -> BotSchema:
        if not isinstance(bot_token, str) and fullmatch(r"\d{10}:\w{35}", bot_token):
            raise InvalidParameterFormat(
                "bot_token must be type of str with format 0000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA.")

        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Bot).where(Bot.bot_token == bot_token))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise BotNotFound(f"token {bot_token} not found in database.")

        return BotSchema.model_validate(res)

    async def add_bot(self, bot: BotSchema) -> None:
        if not isinstance(bot, BotSchema):
            raise InvalidParameterFormat("user must be type of database.DbBot.")
        try:
            if await self.get_bot(bot_token=bot.token):
                raise InstanceAlreadyExists(f"bot with {bot.token} already exists in db.")
        except:
            pass

        async with self.engine.begin() as conn:
            raw_res = await conn.execute(insert(Bot).values(**bot.model_dump(by_alias=True)))
        await self.engine.dispose()

        logger.debug(f"successfully add bot with token {bot.token} to db.")

    async def update_bot(self, updated_bot: BotSchema) -> None:
        if not isinstance(updated_bot, BotSchema):
            raise InvalidParameterFormat("updated_user must be type of database.DbBot.")

        async with self.engine.begin() as conn:
            await conn.execute(update(Bot).where(Bot.bot_token == updated_bot.token).
                               values(**updated_bot.model_dump(by_alias=True)))
        await self.engine.dispose()

        logger.debug(f"successfully update bot with token {updated_bot.token} in db.")

    async def del_bot(self, bot_token: str) -> None:
        if not isinstance(bot_token, str) and fullmatch(r"\d{10}:\w{35}", bot_token):
            raise InvalidParameterFormat(
                "bot_token must be type of str with format 0000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA.")
        async with self.engine.begin() as conn:
            await conn.execute(delete(Bot).where(Bot.bot_token == bot_token))

        await self.engine.dispose()

        logger.debug(f"successfully delete bot with token {bot_token} from db.")

