from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, ForeignKeyConstraint, String, \
    DateTime, update
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.channel_post_model import ChannelPost
from database.models.dao import Dao
from logs.config import extra_params


class ChannelPostMediaFileNotFound(Exception):
    """Raised when provided ChannelPostMediaFile not found in database"""
    pass


class ChannelPostMediaFile(Base):
    __tablename__ = "channel_post_media_files"

    channel_post_id = Column(BigInteger, ForeignKey(
        ChannelPost.channel_post_id, ondelete="CASCADE"), primary_key=True)
    file_id_main_bot = Column(String, primary_key=True)
    file_id_custom_bot = Column(String, default=None)
    file_path = Column(String)
    media_type = Column(String, nullable=False)


class ChannelPostMediaFileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_post_id: int = Field(frozen=True)
    file_id_main_bot: str = Field(frozen=True)
    file_id_custom_bot: str | None = None
    file_path: str
    media_type: str


class ChannelPostMediaFileDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_channel_post_media_files(self, channel_post_id: int) -> list[ChannelPostMediaFileSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ChannelPostMediaFile).where(
                    ChannelPostMediaFile.channel_post_id == channel_post_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for channel_post_media_file in raw_res:
            res.append(ChannelPostMediaFileSchema.model_validate(
                channel_post_media_file))

        self.logger.debug(
            f"channel_post_id={channel_post_id}: has {len(res)} media_files",
            extra=extra_params(channel_post_id=channel_post_id)
        )

        return res

    @validate_call
    async def add_channel_post_media_file(self, new_channel_post_media_file: ChannelPostMediaFileSchema) -> None:
        if type(new_channel_post_media_file) != ChannelPostMediaFileSchema:
            raise InvalidParameterFormat(
                "new_channel_post_media_file must be type of ChannelPostMediaFileSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                insert(ChannelPostMediaFile).values(
                    new_channel_post_media_file.model_dump())
            )

        self.logger.debug(
            f"channel_post_id={new_channel_post_media_file.channel_post_id}: media file {new_channel_post_media_file.file_id_main_bot} is added",
            extra=extra_params(
                channel_post_id=new_channel_post_media_file.channel_post_id)
        )

    @validate_call
    async def update_media_file(self, new_channel_post_media_file: ChannelPostMediaFileSchema) -> None:
        if type(new_channel_post_media_file) != ChannelPostMediaFileSchema:
            raise InvalidParameterFormat(
                "new_channel_post_media_file must be type of ChannelPostMediaFileSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                update(ChannelPostMediaFile).where(
                    ChannelPostMediaFile.file_id_main_bot == new_channel_post_media_file.file_id_main_bot
                ).values(new_channel_post_media_file.model_dump())
            )

        self.logger.debug(
            f"channel_post_id={new_channel_post_media_file.channel_post_id}: media file {new_channel_post_media_file.file_id_main_bot} is updated",
            extra=extra_params(
                channel_post_id=new_channel_post_media_file.channel_post_id)
        )

    @validate_call
    async def delete_channel_post_media_files(self, channel_post_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(ChannelPostMediaFile).where(
                    ChannelPostMediaFile.channel_post_id == channel_post_id,
                )
            )

        self.logger.debug(
            f"channel_post_id={channel_post_id}: all media files are deleted",
            extra=extra_params(channel_post_id=channel_post_id)
        )
