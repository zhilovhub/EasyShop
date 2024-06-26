import datetime
from typing import Optional

from pydantic import BaseModel, Field, validate_call, ConfigDict

from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, String, DateTime, update
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot

from logs.config import extra_params


class MailingNotFound(Exception):
    """Raised when provided Mailing not found in database"""
    pass


class Mailing(Base):
    __tablename__ = "mailings"

    mailing_id = Column(BigInteger, autoincrement=True, primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), nullable=False)

    description = Column(String)
    is_sent = Column(BOOLEAN, default=False)

    has_button = Column(BOOLEAN, default=False)
    button_text = Column(String, default="Shop")
    button_url = Column(String)

    created_at = Column(DateTime, nullable=False)

    # Extra settings
    enable_notification_sound = Column(BOOLEAN, default=True)
    enable_link_preview = Column(BOOLEAN, default=False)

    # Mailing Stats
    is_running = Column(BOOLEAN, default=False)
    sent_mailing_amount = Column(BigInteger, default=0)

    # Delay
    is_delayed = Column(BOOLEAN, default=False)
    send_date = Column(DateTime, nullable=True)
    job_id = Column(String, nullable=True)


class MailingSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)

    description: Optional[str | None] = None
    is_sent: bool = False

    has_button: bool = False
    button_text: Optional[str | None] = None
    button_url: Optional[str | None] = None

    created_at: datetime.datetime = datetime.datetime.now().replace(tzinfo=None)

    enable_notification_sound: bool = True
    enable_link_preview: bool = False

    is_running: bool = False
    sent_mailing_amount: int = 0

    is_delayed: bool = False
    send_date: Optional[datetime.datetime | None] = None
    job_id: Optional[str | None] = None


class MailingSchema(MailingSchemaWithoutId):
    mailing_id: int = Field(frozen=True)


class MailingDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_mailing(self, mailing_id: int) -> MailingSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Mailing).where(Mailing.mailing_id == mailing_id, Mailing.is_sent == False)  # noqa: E712
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise MailingNotFound

        res = MailingSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: mailing {res.mailing_id} is found",
            extra=extra_params(mailing_id=mailing_id, bot_id=res.bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_mailing_by_bot_id(self, bot_id: int) -> MailingSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Mailing).where(Mailing.bot_id == bot_id, Mailing.is_sent == False)  # noqa: E712
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise MailingNotFound

        res = MailingSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: mailing {res.mailing_id} is found",
            extra=extra_params(mailing_id=res.mailing_id, bot_id=bot_id)
        )

        return res

    @validate_call
    async def add_mailing(self, new_mailing: MailingSchemaWithoutId) -> int:
        if type(new_mailing) != MailingSchemaWithoutId:
            raise InvalidParameterFormat(
                "new_mailing must be type of MailingSchema")

        async with self.engine.begin() as conn:
            mailing_id = (await conn.execute(insert(Mailing).values(new_mailing.model_dump()))).inserted_primary_key[0]

        self.logger.debug(
            f"bot_id={new_mailing.bot_id}: mailing_id {mailing_id} is added",
            extra=extra_params(mailing_id=mailing_id, bot_id=new_mailing.bot_id)
        )

        return mailing_id

    @validate_call
    async def update_mailing(self, updated_mailing: MailingSchema):
        async with self.engine.begin() as conn:
            await conn.execute(
                update(Mailing).where(
                    Mailing.mailing_id == updated_mailing.mailing_id
                ).values(updated_mailing.model_dump())
            )

        self.logger.debug(
            f"bot_id={updated_mailing.bot_id}: mailing {updated_mailing.mailing_id} is updated",
            extra=extra_params(mailing_id=updated_mailing.mailing_id, bot_id=updated_mailing.bot_id)
        )

    @validate_call
    async def delete_mailing(self, mailing_id: int) -> None:
        if type(mailing_id) != int:
            raise InvalidParameterFormat("new_mailing must be type of int")

        async with self.engine.begin() as conn:
            await conn.execute(
                delete(Mailing).where(
                    Mailing.mailing_id == mailing_id
                )
            )

        self.logger.debug(
            f"mailing_id={mailing_id}: mailing {mailing_id} is deleted",
            extra=extra_params(mailing_id=mailing_id)
        )
