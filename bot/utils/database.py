import datetime
from bot.exceptions.exceptions import *
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, insert, delete, update
from sqlalchemy import Table, Column, Integer, String, JSON, BigInteger, DateTime
from sqlalchemy import MetaData
from bot.config import logger
from bot import config
from pydantic import BaseModel, ConfigDict, UUID4, Field, field_validator
from re import fullmatch


class DbBot(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    token: str = Field(alias="bot_token", frozen=True, max_length=46, min_length=46)
    status: str = Field(max_length=55)
    created_at: datetime.datetime = Field(frozen=True)
    created_by: int = Field(frozen=True)
    settings: dict | None = None
    locale: str = Field()


class AlchemyDB:

    def __init__(self, alchemy_url: str):
        self.metadata = MetaData()

        self.bots = Table('bots', self.metadata,
                          Column('bot_token', String(46), primary_key=True),
                          Column('status', String(55), nullable=False),
                          Column('created_at', DateTime, nullable=False),
                          Column('created_by', BigInteger, nullable=False),
                          Column('settings', JSON),
                          Column('locale', String(10), nullable=False),
                          )
        self.engine = create_async_engine(alchemy_url, echo=config.DEBUG)

    async def connect(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(self.metadata.create_all)
        await self.engine.dispose()
        logger.info("bot db connected.")

    # === Bots methods ===

    async def get_bots(self, user_id: int | None = None) -> list[DbBot]:
        async with self.engine.begin() as conn:
            if user_id:
                raw_res = await conn.execute(select(self.bots).where(self.bots.c.created_by == user_id))
            else:
                raw_res = await conn.execute(select(self.bots))
        await self.engine.dispose()
        raw_res = raw_res.fetchall()
        res = []
        for bot in raw_res:
            res.append(DbBot(**bot._mapping))
        return res

    async def get_bot(self, bot_token: str) -> DbBot:
        if not isinstance(bot_token, str) and fullmatch(r"\d{10}:\w{35}", bot_token):
            raise InvalidParameterFormat(
                "bot_token must be type of str with format 0000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA.")
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(self.bots).where(self.bots.c.bot_token == bot_token))
        await self.engine.dispose()
        res = raw_res.fetchone()
        if res is None:
            raise BotNotFound(f"token {bot_token} not found in database.")
        return DbBot(**res._mapping)

    async def add_bot(self, bot: DbBot) -> None:
        if not isinstance(bot, DbBot):
            raise InvalidParameterFormat("user must be type of database.DbBot.")
        try:
            if await self.get_bot(bot_token=bot.token):
                raise InstanceAlreadyExists(f"bot with {bot.token} already exists in db.")
        except:
            pass
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(insert(self.bots).values(**bot.model_dump(by_alias=True)))
        await self.engine.dispose()
        logger.debug(f"successfully add bot with token {bot.token} to db.")

    async def update_bot(self, updated_bot: DbBot) -> None:
        if not isinstance(updated_bot, DbBot):
            raise InvalidParameterFormat("updated_user must be type of database.DbBot.")
        async with self.engine.begin() as conn:
            await conn.execute(update(self.bots).where(self.bots.c.bot_token == updated_bot.token).
                               values(**updated_bot.model_dump(by_alias=True)))
        await self.engine.dispose()
        logger.debug(f"successfully update bot with token {updated_bot.token} in db.")

    async def del_bot(self, bot_token: str) -> None:
        if not isinstance(bot_token, str) and fullmatch(r"\d{10}:\w{35}", bot_token):
            raise InvalidParameterFormat(
                "bot_token must be type of str with format 0000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA.")
        async with self.engine.begin() as conn:
            await conn.execute(delete(self.bots).where(self.bots.c.bot_token == bot_token))
        await self.engine.dispose()
        logger.debug(f"successfully delete bot with token {bot_token} from db.")
