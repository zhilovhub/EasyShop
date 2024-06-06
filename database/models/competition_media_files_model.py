from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, ForeignKeyConstraint, String, \
    DateTime
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.competition_model import Competition
from database.models.dao import Dao
from logs.config import extra_params


class CompetitionMediaFileNotFound(Exception):
    """Raised when provided CompetitionMediaFile not found in database"""
    pass


class CompetitionMediaFile(Base):
    __tablename__ = "competition_media_files"

    competition_id = Column(BigInteger, ForeignKey(Competition.competition_id, ondelete="CASCADE"), primary_key=True)
    file_name = Column(String, primary_key=True)
    media_type = Column(String, nullable=False)


class CompetitionMediaFileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    competition_id: int = Field(frozen=True)
    file_name: str = Field(frozen=True)
    media_type: str


class CompetitionMediaFileDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_competition_media_files(self, competition_id: int) -> list[CompetitionMediaFileSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(CompetitionMediaFile).where(CompetitionMediaFile.competition_id == competition_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for competition_media_file in raw_res:
            res.append(CompetitionMediaFileSchema.model_validate(competition_media_file))

        self.logger.debug(
            f"competition_id={competition_id}: has {len(res)} media_files",
            extra=extra_params(competition_id=competition_id)
        )
        return res

    @validate_call
    async def add_competition_media_file(self, new_competition_media_file: CompetitionMediaFileSchema) -> None:
        if type(new_competition_media_file) != CompetitionMediaFileSchema:
            raise InvalidParameterFormat("new_competition_media_file must be type of CompetitionMediaFileSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                insert(CompetitionMediaFile).values(new_competition_media_file.model_dump())
            )

        self.logger.debug(
            f"competition_media_file={new_competition_media_file.file_name}: is added to database",
            extra=extra_params(competition_id=new_competition_media_file.competition_id)
        )

    @validate_call
    async def delete_competition_media_files(self, competition_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(CompetitionMediaFile).where(
                    CompetitionMediaFile.competition_id == competition_id,
                )
            )

        self.logger.debug(
            f"competition_id={competition_id}: all media files are deleted",
            extra=extra_params(competition_id=competition_id)
        )
