import datetime
from typing import Optional

from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, ForeignKeyConstraint, String, \
    DateTime, update
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.bot_model import Bot
from database.models.dao import Dao
from enum import Enum


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


class MailingSchema(MailingSchemaWithoutId):
    mailing_id: int = Field(frozen=True)


class MailingDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_mailing(self, mailing_id: int) -> MailingSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Mailing).where(Mailing.mailing_id == mailing_id, Mailing.is_sent == False))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise MailingNotFound

        self.logger.info(
            f"get_mailing method with mailing_id: {mailing_id} success.")
        return MailingSchema.model_validate(raw_res)

    @validate_call(validate_return=True)
    async def get_mailing_by_bot_id(self, bot_id: int) -> MailingSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Mailing).where(Mailing.bot_id == bot_id, Mailing.is_sent == False))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise MailingNotFound

        self.logger.info(f"get_mailing method with bot_id: {bot_id} success.")
        return MailingSchema.model_validate(raw_res)

    @validate_call
    async def add_mailing(self, new_mailing: MailingSchemaWithoutId) -> int:
        if type(new_mailing) != MailingSchemaWithoutId:
            raise InvalidParameterFormat(
                "new_mailing must be type of MailingSchema")

        async with self.engine.begin() as conn:
            mailing_id = (await conn.execute(insert(Mailing).values(new_mailing.model_dump()))).inserted_primary_key[0]

        self.logger.info(
            f"successfully add mailing with mailing_id for mailing_id {mailing_id} for bot_id {new_mailing.bot_id} to db"
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
        self.logger.info(
            f"successfully update mailing with id {updated_mailing.mailing_id} at db.")

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

        self.logger.info(
            f"successfully deleted mailing with mailing_id {mailing_id} from db"
        )
