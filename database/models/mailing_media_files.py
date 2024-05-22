from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, ForeignKeyConstraint, String, \
    DateTime
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.mailing_model import Mailing
from database.models.dao import Dao


class MailingMediaFileNotFound(Exception):
    """Raised when provided MailingMediaFile not found in database"""
    pass


class MailingMediaFile(Base):
    __tablename__ = "mailing_media_files"

    mailing_id = Column(BigInteger, ForeignKey(Mailing.mailing_id, ondelete="CASCADE"), primary_key=True)
    file_name = Column(String, primary_key=True)
    media_type = Column(String, nullable=False)


class MailingMediaFileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mailing_id: int = Field(frozen=True)
    file_name: str = Field(frozen=True)
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

        self.logger.info(f"get_all_mailing_media_files method with mailing_id: {mailing_id} success")
        return res

    @validate_call
    async def add_mailing_media_file(self, new_mailing_media_file: MailingMediaFileSchema) -> None:
        if type(new_mailing_media_file) != MailingMediaFileSchema:
            raise InvalidParameterFormat("new_mailing_media_file must be type of MailingMediaFileSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                insert(MailingMediaFile).values(new_mailing_media_file.model_dump())
            )

        self.logger.info(
            f"successfully add mailing_media_files with mailing_id {new_mailing_media_file.mailing_id}"
        )

    @validate_call
    async def delete_mailing_media_files(self, mailing_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(MailingMediaFile).where(
                    MailingMediaFile.mailing_id == mailing_id,
                )
            )
        self.logger.info(f"deleted mailing_media_files with mailing_id {mailing_id}")
