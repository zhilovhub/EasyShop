from datetime import datetime

from sqlalchemy import BigInteger, Column, String, DateTime, JSON
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict

from database.models import Base
from database.models.dao import Dao

from bot.config import logger
from bot.exceptions.exceptions import *


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    status = Column(String(55), nullable=False)
    registered_at = Column(DateTime, nullable=False)
    settings = Column(JSON)
    locale = Column(String(10), nullable=False)


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(alias="user_id", frozen=True)
    status: str = Field(max_length=55)
    registered_at: datetime = Field(frozen=True)
    settings: dict | None = None
    locale: str = Field(max_length=10, default="default")


class UserDao(Dao):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)
        
    async def get_users(self) -> list[UserSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(User))
        await self.engine.dispose()
        
        raw_res = raw_res.fetchall()
        res = []
        for user in raw_res:
            res.append(UserSchema.model_validate(user))
            
        return res
    
    async def get_user(self, user_id: int) -> UserSchema:
        if not isinstance(user_id, int):
            raise InvalidParameterFormat("user_id must be type of int.")
        
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(User).where(User.user_id == user_id))
        await self.engine.dispose()
        
        res = raw_res.fetchone()
        if res is None:
            raise UserNotFound(f"id {user_id} not found in database.")
        
        return UserSchema.model_validate(res)

    async def add_user(self, user: UserSchema) -> None:
        if not isinstance(user, UserSchema):
            raise InvalidParameterFormat("user must be type of database.DbUser.")
        try:
            if await self.get_user(user_id=user.id):
                raise InstanceAlreadyExists(f"user with {user.id} already exists in db.")
        except:
            pass

        async with self.engine.begin() as conn:
            await conn.execute(insert(User).values(**user.model_dump(by_alias=True)))
        await self.engine.dispose()

        logger.debug(f"successfully add user with id {user.id} to db.")

    async def update_user(self, updated_user: UserSchema) -> None:
        if not isinstance(updated_user, UserSchema):
            raise InvalidParameterFormat("updated_user must be type of database.DbUser.")

        async with self.engine.begin() as conn:
            await conn.execute(update(User).where(User.user_id == updated_user.id).
                               values(**updated_user.model_dump(by_alias=True)))
        await self.engine.dispose()

        logger.debug(f"successfully update user with id {updated_user.id} in db.")

    async def del_user(self, user_id: int) -> None:
        if not isinstance(user_id, int):
            raise InvalidParameterFormat("user_id must be type of int.")

        async with self.engine.begin() as conn:
            await conn.execute(delete(User).where(User.user_id == user_id))
        await self.engine.dispose()

        logger.debug(f"successfully delete user with id {user_id} from db.")
