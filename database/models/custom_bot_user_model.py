from sqlalchemy import BigInteger, Column, String
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field

from database.models import Base
from database.models.dao import Dao


class CustomBotUser(Base):
    __tablename__ = "custom_bot_users"

    user_id = Column("user_id", BigInteger, primary_key=True)
    status = Column("status", String(55))


class CustomBotUserSchema(BaseModel):
    user_id: str
    status: str = Field(max_length=55)


class CustomBotUserDao(Dao):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)
