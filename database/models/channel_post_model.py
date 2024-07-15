from pydantic import BaseModel, Field, validate_call, ConfigDict

from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncEngine


from database.models import Base
from database.models.dao import Dao
from database.exceptions import InvalidParameterFormat
from database.models.bot_model import Bot
from database.models.post_message_model import PostMessage

from logs.config import extra_params


class ChannelPostNotFound(Exception):
    """Raised when provided channel_post not found in database"""
    pass


class ChannelPost(Base):
    __tablename__ = "channel_posts"
    channel_post_id = Column(BigInteger, primary_key=True, unique=True)

    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"))
    post_message_id = Column(ForeignKey(PostMessage.post_message_id, ondelete="CASCADE"))


class ChannelPostSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)

    post_message_id: int = Field(frozen=True)


class ChannelPostSchema(ChannelPostSchemaWithoutId):
    channel_post_id: int = Field(frozen=True)


class ChannelPostDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_channel_posts(self, bot_id: int) -> list[ChannelPostSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ChannelPost).where(ChannelPost.bot_id == bot_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for channel_post in raw_res:
            res.append(ChannelPostSchema.model_validate(channel_post))

        self.logger.debug(
            f"bot_id={bot_id}: has {len(res)} channel_posts",
            extra=extra_params(bot_id=bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_channel_post_by_post_message_id(self, post_message_id: int) -> ChannelPostSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(ChannelPost).where(ChannelPost.post_message_id == post_message_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ChannelPostNotFound

        res = ChannelPostSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: channel_post is found: {res}",
            extra=extra_params(bot_id=res.bot_id, channel_post_id=res.channel_post_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_channel_post_by_bot_id(self, bot_id: int) -> ChannelPostSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(ChannelPost).where(ChannelPost.bot_id == bot_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ChannelPostNotFound

        res = ChannelPostSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: channel_post is found: {res}",
            extra=extra_params(bot_id=res.bot_id, channel_post_id=res.channel_post_id)
        )

        return res

    @validate_call
    async def add_channel_post(self, new_channel_post: ChannelPostSchemaWithoutId) -> int:
        if not isinstance(new_channel_post, ChannelPostSchemaWithoutId):
            raise InvalidParameterFormat(
                "new_channel_post must be type of ChannelPostSchemaWithoutId")

        async with self.engine.begin() as conn:
            channel_post_id = (
                await conn.execute(insert(ChannelPost).values(new_channel_post.model_dump()))
            ).inserted_primary_key[0]

        self.logger.debug(
            f"bot_id={new_channel_post.bot_id}: channel_post {channel_post_id} is added",
            extra=extra_params(bot_id=new_channel_post.bot_id, channel_post_id=channel_post_id)
        )

        return channel_post_id

    @validate_call
    async def update_channel_post(self, updated_channel_post: ChannelPostSchema) -> None:
        if not isinstance(updated_channel_post, ChannelPostSchema):
            raise InvalidParameterFormat(
                "new_channel_post must be type of ChannelPostSchema")
        async with self.engine.begin() as conn:
            await conn.execute(
                update(ChannelPost).where(
                    ChannelPost.channel_post_id == updated_channel_post.channel_post_id
                ).values(**updated_channel_post.model_dump(by_alias=True))
            )
        await self.engine.dispose()

        self.logger.debug(
            f"channel_post_id={updated_channel_post.channel_post_id}: "
            f"channel_post {updated_channel_post.channel_post_id} is updated",
            extra=extra_params(channel_post_id=updated_channel_post.channel_post_id, bot_id=updated_channel_post.bot_id)
        )

    @validate_call
    async def delete_channel_post(self, channel_post: ChannelPostSchema) -> None:
        if not isinstance(channel_post, ChannelPostSchema):
            raise InvalidParameterFormat(
                "new_channel_post must be type of ChannelPostSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                delete(ChannelPost).where(
                    ChannelPost.channel_post_id == channel_post.channel_post_id
                )
            )

        self.logger.debug(
            f"bot_id={channel_post.bot_id}: channel_post {channel_post.channel_post_id} is deleted",
            extra=extra_params(bot_id=channel_post.bot_id,
                               channel_post_id=channel_post.channel_post_id)
        )
