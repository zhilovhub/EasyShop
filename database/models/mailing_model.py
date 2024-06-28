from pydantic import BaseModel, Field, validate_call, ConfigDict

from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot
from database.models.post_message_model import PostMessage

from logs.config import extra_params


class MailingNotFound(Exception):
    """Raised when provided mailing not found in database"""
    pass


class Mailing(Base):
    __tablename__ = "mailings"
    mailing_id = Column(BigInteger, primary_key=True, unique=True)

    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"))
    post_message_id = Column(ForeignKey(PostMessage.post_message_id, ondelete="CASCADE"))


class MailingSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)

    post_message_id = Field(frozen=True)


class MailingSchema(MailingSchemaWithoutId):
    mailing_id: int = Field(frozen=True)


class MailingDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_mailings(self, bot_id: int) -> list[MailingSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Mailing).where(Mailing.bot_id == bot_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for mailing in raw_res:
            res.append(MailingSchema.model_validate(mailing))

        self.logger.debug(
            f"bot_id={bot_id}: has {len(res)} mailings",
            extra=extra_params(bot_id=bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_mailing_by_mailing_id(self, mailing_id: int) -> MailingSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Mailing).where(Mailing.mailing_id == mailing_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise MailingNotFound

        res = MailingSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: mailing {mailing_id} is found",
            extra=extra_params(bot_id=res.bot_id, mailing_id=mailing_id)
        )

        return res

    @validate_call
    async def add_mailing(self, new_mailing: MailingSchemaWithoutId) -> int:
        if not isinstance(new_mailing, MailingSchemaWithoutId):
            raise InvalidParameterFormat(
                "new_mailing must be type of MailingSchemaWithoutId")

        async with self.engine.begin() as conn:
            mailing_id = (
                await conn.execute(insert(MailingSchemaWithoutId).values(new_mailing.model_dump()))
            ).inserted_primary_key[0]

        self.logger.debug(
            f"bot_id={new_mailing.bot_id}: mailing {mailing_id} is added",
            extra=extra_params(bot_id=new_mailing.bot_id, mailing_id=mailing_id)
        )

        return mailing_id

    @validate_call
    async def update_mailing(self, updated_mailing: MailingSchema) -> None:
        if not isinstance(updated_mailing, MailingSchema):
            raise InvalidParameterFormat(
                "new_mailing must be type of MailingSchema")
        async with self.engine.begin() as conn:
            await conn.execute(update(Mailing).where(Mailing.mailing_id == updated_mailing.mailing_id).
                               values(**updated_mailing.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"mailing_id={updated_mailing.mailing_id}: mailing {updated_mailing.mailing_id} is updated",
            extra=extra_params(mailing_id=updated_mailing.mailing_id, bot_id=updated_mailing.bot_id)
        )

    @validate_call
    async def delete_mailing(self, mailing: MailingSchema) -> None:
        if not isinstance(mailing, MailingSchema):
            raise InvalidParameterFormat(
                "new_mailing must be type of MailingSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                delete(Mailing).where(
                    Mailing.mailing_id == mailing.mailing_id
                )
            )

        self.logger.debug(
            f"bot_id={mailing.bot_id}: mailing {mailing.mailing_id} is deleted",
            extra=extra_params(bot_id=mailing.bot_id,
                               mailing_id=mailing.mailing_id)
        )
