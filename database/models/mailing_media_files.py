from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, ForeignKeyConstraint, String, \
    DateTime, update
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.mailing_model import Mailing
from database.models.dao import Dao
from logs.config import extra_params


class MailingMediaFileNotFound(Exception):
    """Raised when provided MailingMediaFile not found in database"""
    pass


class MailingMediaFile(Base):
    __tablename__ = "mailing_media_files"

    mailing_id = Column(BigInteger, ForeignKey(Mailing.mailing_id, ondelete="CASCADE"), primary_key=True)
    file_id_main_bot = Column(String, primary_key=True)
    file_id_custom_bot = Column(String, default=None)
    file_path = Column(String)
    media_type = Column(String, nullable=False)


class MailingMediaFileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mailing_id: int = Field(frozen=True)
    file_id_main_bot: str = Field(frozen=True)
    file_id_custom_bot: str | None = None
    file_path: str
    media_type: str


class MailingMediaFileDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_mailing_media_files(self, mailing_id: int) -> list[MailingMediaFileSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(MailingMediaFile).where(MailingMediaFile.mailing_id == mailing_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for mailing_media_file in raw_res:
            res.append(MailingMediaFileSchema.model_validate(mailing_media_file))

        self.logger.debug(
            f"mailing_id={mailing_id}: has {len(res)} media_files",
            extra=extra_params(mailing_id=mailing_id)
        )

        return res

    @validate_call
    async def add_mailing_media_file(self, new_mailing_media_file: MailingMediaFileSchema) -> None:
        if type(new_mailing_media_file) != MailingMediaFileSchema:
            raise InvalidParameterFormat("new_mailing_media_file must be type of MailingMediaFileSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                insert(MailingMediaFile).values(new_mailing_media_file.model_dump())
            )

        self.logger.debug(
            f"mailing_id={new_mailing_media_file.mailing_id}: media file {new_mailing_media_file.file_id_main_bot} is added",
            extra=extra_params(mailing_id=new_mailing_media_file.mailing_id)
        )

    @validate_call
    async def update_media_file(self, new_mailing_media_file: MailingMediaFileSchema) -> None:
        if type(new_mailing_media_file) != MailingMediaFileSchema:
            raise InvalidParameterFormat("new_mailing_media_file must be type of MailingMediaFileSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                update(MailingMediaFile).where(
                    MailingMediaFile.file_id_main_bot == new_mailing_media_file.file_id_main_bot
                ).values(new_mailing_media_file.model_dump())
            )

        self.logger.debug(
            f"mailing_id={new_mailing_media_file.mailing_id}: media file {new_mailing_media_file.file_id_main_bot} is updated",
            extra=extra_params(mailing_id=new_mailing_media_file.mailing_id)
        )

    @validate_call
    async def delete_mailing_media_files(self, mailing_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(MailingMediaFile).where(
                    MailingMediaFile.mailing_id == mailing_id,
                )
            )

        self.logger.debug(
            f"mailing_id={mailing_id}: all media files are deleted",
            extra=extra_params(mailing_id=mailing_id)
        )
