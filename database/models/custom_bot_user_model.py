from pydantic import BaseModel, ConfigDict, validate_call

from sqlalchemy import BigInteger, Column, ForeignKey, insert, select, update, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot
from database.exceptions.exceptions import KwargsException

from database.enums import UserLanguage, UserLanguageValues

from logs.config import extra_params


class CustomBotUserNotFoundError(KwargsException):
    """Raised when provided custom user not found in database"""


class CustomBotUser(Base):
    __tablename__ = "custom_bot_users"

    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    balance = Column(BigInteger, default=0)
    user_language = Column(UserLanguage, nullable=False, default=UserLanguageValues.RUSSIAN)


class CustomBotUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int
    user_id: int
    balance: int | None = 0
    user_language: UserLanguageValues = UserLanguageValues.RUSSIAN


class CustomBotUserDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_custom_bot_user(self, bot_id: int, user_id: int) -> CustomBotUserSchema:  # TODO write tests
        """
        :raises CustomBotUserNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(CustomBotUser).where(CustomBotUser.bot_id == bot_id, CustomBotUser.user_id == user_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise CustomBotUserNotFoundError(user_id=user_id, bot_id=bot_id)

        res = CustomBotUserSchema.model_validate(res)

        self.logger.debug(f"bot_id={bot_id}: found user {res}", extra=extra_params(user_id=user_id, bot_id=bot_id))

        return res

    @validate_call(validate_return=True)
    async def get_custom_bot_users(self, bot_id: int) -> list[CustomBotUserSchema]:  # TODO write tests
        """
        Returns users belonging to Bot
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(CustomBotUser).where(CustomBotUser.bot_id == bot_id))
        await self.engine.dispose()

        users = []
        for raw in raw_res.fetchall():
            users.append(CustomBotUserSchema.model_validate(raw))

        self.logger.debug(f"bot_id={bot_id}: has {len(users)} users", extra=extra_params(bot_id=bot_id))

        return users

    @validate_call(validate_return=True)
    async def update_custom_bot_user(self, updated_user: CustomBotUserSchema):
        """
        Updates Custom User
        """
        async with self.engine.begin() as conn:
            await conn.execute(
                update(CustomBotUser)
                .where(CustomBotUser.user_id == updated_user.user_id)
                .values(**updated_user.model_dump(by_alias=True))
            )
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={updated_user.user_id}, bot_id={updated_user.bot_id}: " f"updated custom bot user {updated_user}",
            extra=extra_params(user_id=updated_user.user_id, bot_id=updated_user.bot_id),
        )

    @validate_call(validate_return=True)
    async def add_custom_bot_user(
        self, bot_id: int, user_id: int, lang: UserLanguageValues = UserLanguageValues.RUSSIAN
    ) -> None:
        """
        :raises IntegrityError:
        """
        async with self.engine.begin() as conn:
            await conn.execute(insert(CustomBotUser).values(bot_id=bot_id, user_id=user_id, user_language=lang))
        await self.engine.dispose()

        self.logger.debug(f"bot_id={bot_id}: added user {user_id}", extra=extra_params(user_id=user_id, bot_id=bot_id))

    @validate_call(validate_return=True)
    async def delete_custom_bot_user(self, bot_id: int, user_id: int) -> None:
        """
        Deletes Custom bot user from db
        """
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(CustomBotUser).where(CustomBotUser.bot_id == bot_id, CustomBotUser.user_id == user_id)
            )
        await self.engine.dispose()

        self.logger.debug(
            f"bot_id={bot_id}: deleted user {user_id}", extra=extra_params(user_id=user_id, bot_id=bot_id)
        )
