from datetime import datetime

from aiogram.utils.token import validate_token

from sqlalchemy import BigInteger, Column, String, DateTime, JSON, ForeignKey
from sqlalchemy import select, update, delete, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict, validate_call

from database.models import Base
from database.models.dao import Dao
from database.models.user_model import User
from database.models.option_model import Option
from database.exceptions.exceptions import KwargsException

from logs.config import extra_params


class BotNotFoundError(KwargsException):
    """Raised when provided bot not found in database"""


class BotIntegrityError(KwargsException):
    """Raised when there is an IntegrityError with provided bot and hides the token"""
    # TODO hide bot_token


class Bot(Base):
    __tablename__ = "bots"

    bot_id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_token = Column(String(46), unique=True)
    status = Column(String(55), nullable=False)
    created_at = Column(DateTime, nullable=False)
    created_by = Column(ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False)
    settings = Column(JSON, nullable=True)
    options_id = Column(ForeignKey(Option.id, ondelete="CASCADE"), nullable=True)
    locale = Column(String(10), nullable=False)
    admin_invite_link_hash = Column(String(15), unique=True)


class BotSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    token: str = Field(alias="bot_token", frozen=True, max_length=46, min_length=46)
    status: str = Field(max_length=55)
    created_at: datetime = Field(frozen=True)
    created_by: int = Field(frozen=True)
    settings: dict | None = None
    options_id: int
    locale: str = Field()
    admin_invite_link_hash: str | None = Field(max_length=15, default=None)


class BotSchema(BotSchemaWithoutId):
    bot_id: int = Field(frozen=True)


class BotDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_bots(self, user_id: int | None = None) -> list[BotSchema]:
        """
        :param user_id: user_id of user
        :return: The list of the BotSchema
        """
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

    @validate_call(validate_return=True)
    async def get_bot(self, bot_id: int) -> BotSchema:
        """
        :param bot_id: bot_id of the bot
        :return: BotSchema with specific bot_id

        :raises BotNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Bot).where(Bot.bot_id == bot_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise BotNotFoundError(bot_id=bot_id)

        self.logger.debug(
            f"bot_id={bot_id}: bot {bot_id} is found",
            extra=extra_params(bot_id=bot_id)
        )

        return BotSchema.model_validate(res)

    @validate_call(validate_return=True)
    async def get_bot_by_invite_link_hash(self, link_hash: str) -> BotSchema:
        """
        :raises BotNotFoundError
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Bot).where(Bot.admin_invite_link_hash == link_hash))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise BotNotFoundError(link_hash=link_hash)

        return BotSchema.model_validate(res)

    @validate_call(validate_return=True)
    async def get_bot_by_created_by(self, created_by: int) -> BotSchema:
        """
        :param created_by: user_id of the owner of the bot
        :return: BotSchema

        :raises BotNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Bot).where(Bot.created_by == created_by))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise BotNotFoundError(created_by=created_by)

        res = BotSchema.model_validate(res)

        self.logger.debug(
            f"bot_id={res.bot_id}: bot with created_by={created_by} is found",
            extra=extra_params(bot_id=res.bot_id, user_id=created_by)
        )

        return res

    @validate_call(validate_return=True)
    async def get_bot_by_token(self, bot_token: str) -> BotSchema:
        """
        :param bot_token: telegram token of the Bot
        :return: BotSchema

        :raises BotNotFoundError:
        :raises TokenValidationError:
        """
        validate_token(bot_token)

        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Bot).where(Bot.bot_token == bot_token))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise BotNotFoundError(bot_token=bot_token)

        res = BotSchema.model_validate(res)

        self.logger.debug(
            f"bot_id={res.bot_id}: bot with bot_token={bot_token} is found",
            extra=extra_params(bot_id=res.bot_id, bot_token=bot_token)
        )

        return res

    @validate_call(validate_return=True)
    async def add_bot(self, bot: BotSchemaWithoutId) -> int:
        """

        :param bot: BotSchema without primary key
        :return: id of inserted Bot

        :raises BotIntegrityError
        """
        async with self.engine.begin() as conn:
            try:
                bot_id = (await conn.execute(insert(Bot).values(
                    **bot.model_dump(by_alias=True))
                )).inserted_primary_key[0]
            except IntegrityError as e:
                raise BotIntegrityError(
                    bot_token=bot.token,
                    e=e
                )

        await self.engine.dispose()

        self.logger.debug(
            f"bot_id={bot_id}: bot {bot_id} is added to",
            extra=extra_params(user_id=bot.created_by, bot_id=bot_id)
        )

        return bot_id

    @validate_call(validate_return=True)
    async def update_bot(self, updated_bot: BotSchema) -> None:
        """

        :param updated_bot: New BotSchema
        :return: None
        """
        async with self.engine.begin() as conn:
            await conn.execute(update(Bot).where(Bot.bot_id == updated_bot.bot_id).
                               values(**updated_bot.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"bot_id={updated_bot.bot_id}: bot {updated_bot.bot_id} is updated",
            extra=extra_params(user_id=updated_bot.created_by, bot_id=updated_bot.bot_id)
        )

    @validate_call(validate_return=True)
    async def del_bot(self, bot_id: int) -> None:
        """

        :param bot_id: bot_id of the BotSchema to delete
        :return: None
        """
        async with self.engine.begin() as conn:
            await conn.execute(delete(Bot).where(Bot.bot_id == bot_id))
        await self.engine.dispose()

        self.logger.debug(
            f"bot_id={bot_id}: bot {bot_id} is deleted",
            extra=extra_params(bot_id=bot_id)
        )
