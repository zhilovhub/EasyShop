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


class PostMessageNotFound(Exception):
    """Raised when provided PostMessage not found in database"""
    pass


class PostMessage(Base):
    __tablename__ = "post_message"

    post_message_id = Column(BigInteger, autoincrement=True, primary_key=True)
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

    # PostMessage Stats
    is_running = Column(BOOLEAN, default=False)
    sent_post_message_amount = Column(BigInteger, default=0)

    # Delay
    is_delayed = Column(BOOLEAN, default=False)
    send_date = Column(DateTime, nullable=True)
    job_id = Column(String, nullable=True)


class PostMessageSchemaWithoutId(BaseModel):
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
    sent_post_message_amount: int = 0

    is_delayed: bool = False
    send_date: Optional[datetime.datetime | None] = None
    job_id: Optional[str | None] = None


class PostMessageSchema(PostMessageSchemaWithoutId):
    post_message_id: int = Field(frozen=True)


class PostMessageDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_post_message(self, post_message_id: int) -> PostMessageSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(PostMessage).where(PostMessage.post_message_id == post_message_id, PostMessage.is_sent == False)  # noqa: E712
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise PostMessageNotFound

        res = PostMessageSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: post_message {res.post_message_id} is found",
            extra=extra_params(post_message_id=post_message_id, bot_id=res.bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_post_message_by_bot_id(self, bot_id: int) -> PostMessageSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(PostMessage).where(PostMessage.bot_id == bot_id, PostMessage.is_sent == False)  # noqa: E712
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise PostMessageNotFound

        res = PostMessageSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: post_message {res.post_message_id} is found",
            extra=extra_params(post_message_id=res.post_message_id, bot_id=bot_id)
        )

        return res

    @validate_call
    async def add_post_message(self, new_post_message: PostMessageSchemaWithoutId) -> int:
        if type(new_post_message) != PostMessageSchemaWithoutId:
            raise InvalidParameterFormat("new_post_message must be type of PostMessageSchema")

        async with self.engine.begin() as conn:
            post_message_id = (
                await conn.execute(insert(PostMessage).values(new_post_message.model_dump()))
            ).inserted_primary_key[0]

        self.logger.debug(
            f"bot_id={new_post_message.bot_id}: post_message_id {post_message_id} is added",
            extra=extra_params(post_message_id=post_message_id, bot_id=new_post_message.bot_id)
        )

        return post_message_id

    @validate_call
    async def update_post_message(self, updated_post_message: PostMessageSchema):
        async with self.engine.begin() as conn:
            await conn.execute(
                update(PostMessage).where(
                    PostMessage.post_message_id == updated_post_message.post_message_id
                ).values(updated_post_message.model_dump())
            )

        self.logger.debug(
            f"bot_id={updated_post_message.bot_id}: post_message {updated_post_message.post_message_id} is updated",
            extra=extra_params(post_message_id=updated_post_message.post_message_id, bot_id=updated_post_message.bot_id)
        )

    @validate_call
    async def delete_post_message(self, post_message_id: int) -> None:
        if type(post_message_id) != int:
            raise InvalidParameterFormat("new_post_message must be type of int")

        async with self.engine.begin() as conn:
            await conn.execute(
                delete(PostMessage).where(
                    PostMessage.post_message_id == post_message_id
                )
            )

        self.logger.debug(
            f"post_message_id={post_message_id}: post_message {post_message_id} is deleted",
            extra=extra_params(post_message_id=post_message_id)
        )
