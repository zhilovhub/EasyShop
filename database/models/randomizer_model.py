from pydantic import BaseModel, Field, ConfigDict

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import BigInteger, Column, ForeignKey, BOOLEAN

from database.models import Base
from database.models.dao import Dao
from database.models.competition_model import Competition


class RandomizerNotFound(Exception):
    """Raised when provided Randomizer not found in database"""
    pass


class Randomizer(Base):
    __tablename__ = "randomizers"

    randomizer_id = Column(BigInteger, autoincrement=True, primary_key=True)
    competition_id = Column(BigInteger, ForeignKey(Competition.competition_id, ondelete="CASCADE"), primary_key=True)

    winners_count = Column(BigInteger, default=1)
    only_with_usernames = Column(BOOLEAN, default=False)


class RandomizerSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    randomizer_id: int = Field(frozen=True)
    competition_id: int = Field(frozen=True)

    winners_count: int = Field(default=1)
    only_with_usernames: bool = Field(default=False)


class RandomizerDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)
