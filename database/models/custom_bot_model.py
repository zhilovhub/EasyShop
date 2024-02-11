from sqlalchemy import BigInteger, Column, String, DateTime, JSON
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field

from database.models import Base
from database.models.dao import Dao

import datetime


class CustomBot(Base):
    __tablename__ = "bots"

    bot_token = Column(String(46), primary_key=True)
    status = Column(String(55), nullable=False)
    created_at = Column(DateTime, nullable=False)
    created_by = Column(BigInteger, nullable=False)
    settings = Column(JSON)
    locale = Column(String(10), nullable=False)


class CustomBotSchema(BaseModel):
    token: str = Field(alias="bot_token", frozen=True, max_length=46, min_length=46)
    status: str = Field(max_length=55)
    created_at: datetime.datetime = Field(frozen=True)
    created_by: int = Field(frozen=True)
    settings: dict | None = None
    locale: str = Field()


class CustomBotDao(Dao):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)
