from pydantic import BaseModel, Field, validate_call, ConfigDict

from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, String, update
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao
from database.exceptions.exceptions import KwargsException
from database.models.post_message_model import PostMessage

from logs.config import extra_params


class PostMessageMediaFileNotFound(KwargsException):
    """Raised when provided PostMessageMediaFile not found in database"""


class PostMessageMediaFile(Base):
    __tablename__ = "post_message_media_files"

    post_message_id = Column(BigInteger, ForeignKey(PostMessage.post_message_id, ondelete="CASCADE"), primary_key=True)
    file_id_main_bot = Column(String, primary_key=True)
    file_id_custom_bot = Column(String, default=None)
    file_path = Column(String)
    media_type = Column(String, nullable=False)


class PostMessageMediaFileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_message_id: int = Field(frozen=True)
    file_id_main_bot: str = Field(frozen=True)
    file_id_custom_bot: str | None = None
    file_path: str
    media_type: str


class PostMessageMediaFileDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_post_message_media_files(self, post_message_id: int) -> list[PostMessageMediaFileSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(PostMessageMediaFile).where(PostMessageMediaFile.post_message_id == post_message_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for post_message_media_file in raw_res:
            res.append(PostMessageMediaFileSchema.model_validate(post_message_media_file))

        self.logger.debug(
            f"post_message_id={post_message_id}: has {len(res)} media_files",
            extra=extra_params(post_message_id=post_message_id),
        )

        return res

    @validate_call(validate_return=True)
    async def add_post_message_media_file(self, new_post_message_media_file: PostMessageMediaFileSchema) -> None:
        """
        :raises IntegrityError:
        """
        async with self.engine.begin() as conn:
            await conn.execute(insert(PostMessageMediaFile).values(new_post_message_media_file.model_dump()))

        self.logger.debug(
            f"post_message_id={new_post_message_media_file.post_message_id}: "
            f"added media file {new_post_message_media_file}",
            extra=extra_params(post_message_id=new_post_message_media_file.post_message_id),
        )

    @validate_call(validate_return=True)
    async def update_media_file(self, new_post_message_media_file: PostMessageMediaFileSchema) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                update(PostMessageMediaFile)
                .where(PostMessageMediaFile.file_id_main_bot == new_post_message_media_file.file_id_main_bot)
                .values(new_post_message_media_file.model_dump())
            )

        self.logger.debug(
            f"post_message_id={new_post_message_media_file.post_message_id}: "
            f"updated media file {new_post_message_media_file}",
            extra=extra_params(post_message_id=new_post_message_media_file.post_message_id),
        )

    @validate_call(validate_return=True)
    async def delete_post_message_media_files(self, post_message_id: int) -> None:
        """
        Deletes all media files

        :param post_message_id: id of PostMessage where to delete all files
        """
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(PostMessageMediaFile).where(
                    PostMessageMediaFile.post_message_id == post_message_id,
                )
            )

        self.logger.debug(
            f"post_message_id={post_message_id}: all media files have been deleted",
            extra=extra_params(post_message_id=post_message_id),
        )
