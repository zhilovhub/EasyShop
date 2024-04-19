from sqlalchemy import BigInteger, Column, String, ForeignKey
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field

from database.models import Base
from database.models.bot_model import Bot
from database.models.dao import Dao


class CustomBotUser(Base):
    __tablename__ = "custom_bot_users"

    bot_id = Column(ForeignKey(Bot.bot_id), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)


class CustomBotUserSchema(BaseModel):
    bot_id: int
    user_id: int


class CustomBotUserDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)
