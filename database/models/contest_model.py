from pydantic import BaseModel, Field, validate_call, ConfigDict

from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, update, Boolean, DateTime, String
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.exc import IntegrityError

from bot.exceptions import InvalidParameterFormat

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot
from database.models.post_message_model import PostMessage

from bot.exceptions.exceptions import InstanceAlreadyExists

from logs.config import extra_params

from datetime import datetime


class ContestNotFound(Exception):
    """Raised when provided contest not found in database"""
    pass


class ContestUserNotFound(Exception):
    """Raised when provided contest user not found in database"""
    pass


class Contest(Base):
    __tablename__ = "contests"
    contest_id = Column(BigInteger, primary_key=True, unique=True)

    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"))
    post_message_id = Column(ForeignKey(PostMessage.post_message_id, ondelete="CASCADE"))
    winners_count = Column(BigInteger)
    is_finished = Column(Boolean)
    finish_date = Column(DateTime)
    finish_job_id = Column(String, nullable=True)
    # winners_list = Column()
    # contest_type = Column()


class ContestUser(Base):
    __tablename__ = "contest_users"
    contest_id = Column(ForeignKey(Contest.contest_id, ondelete="CASCADE"), primary_key=True)
    user_id = Column(BigInteger, nullable=False, primary_key=True)
    join_date = Column(DateTime)
    is_won = Column(Boolean, default=False)
    full_name = Column(String, nullable=True)
    username = Column(String, nullable=True)


class ContestSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)

    post_message_id: int = Field(frozen=True)
    winners_count: int
    is_finished: bool = False
    finish_date: datetime | None = None
    finish_job_id: str | None = None


class ContestSchema(ContestSchemaWithoutId):
    contest_id: int = Field(frozen=True)


class ContestUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contest_id: int = Field(frozen=True)
    user_id: int = Field(frozen=True)
    join_date: datetime
    is_won: bool = False
    full_name: str | None = None
    username: str | None = None


class ContestDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_contests(self, bot_id: int) -> list[ContestSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Contest).where(Contest.bot_id == bot_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for contest in raw_res:
            res.append(ContestSchema.model_validate(contest))

        self.logger.debug(
            f"bot_id={bot_id}: has {len(res)} contests",
            extra=extra_params(bot_id=bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_contest_by_post_message_id(self, post_message_id: int) -> ContestSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Contest).where(Contest.post_message_id == post_message_id, Contest.is_finished == False)  # noqa
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ContestNotFound

        res = ContestSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: contest is found: {res}",
            extra=extra_params(bot_id=res.bot_id, contest_id=res.contest_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_contest_by_bot_id(self, bot_id: int) -> ContestSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Contest).where(Contest.bot_id == bot_id, Contest.is_finished == False)  # noqa
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ContestNotFound

        res = ContestSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: contest is found: {res}",
            extra=extra_params(bot_id=res.bot_id, contest_id=res.contest_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_contest_by_contest_id(self, contest_id: int) -> ContestSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Contest).where(Contest.contest_id == contest_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ContestNotFound

        res = ContestSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: contest is found: {res}",
            extra=extra_params(bot_id=res.bot_id, contest_id=res.contest_id)
        )

        return res

    @validate_call
    async def add_contest(self, new_contest: ContestSchemaWithoutId) -> int:
        if not isinstance(new_contest, ContestSchemaWithoutId):
            raise InvalidParameterFormat(
                "new_contest must be type of ContestSchemaWithoutId")

        async with self.engine.begin() as conn:
            contest_id = (
                await conn.execute(insert(Contest).values(new_contest.model_dump()))
            ).inserted_primary_key[0]

        self.logger.debug(
            f"bot_id={new_contest.bot_id}: contest {contest_id} is added",
            extra=extra_params(bot_id=new_contest.bot_id, contest_id=contest_id)
        )

        return contest_id

    @validate_call
    async def update_contest(self, updated_contest: ContestSchema) -> None:
        if not isinstance(updated_contest, ContestSchema):
            raise InvalidParameterFormat(
                "updated_contest must be type of ContestSchema")
        async with self.engine.begin() as conn:
            await conn.execute(update(Contest).where(Contest.contest_id == updated_contest.contest_id).
                               values(**updated_contest.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"contest_id={updated_contest.contest_id}: contest {updated_contest.contest_id} is updated",
            extra=extra_params(contest_id=updated_contest.contest_id, bot_id=updated_contest.bot_id)
        )

    @validate_call
    async def delete_contest(self, contest: ContestSchema) -> None:
        if not isinstance(contest, ContestSchema):
            raise InvalidParameterFormat(
                "contest must be type of ContestSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                delete(Contest).where(
                    Contest.contest_id == contest.contest_id
                )
            )

        self.logger.debug(
            f"bot_id={contest.bot_id}: contest {contest.contest_id} is deleted",
            extra=extra_params(bot_id=contest.bot_id,
                               contest_id=contest.contest_id)
        )

    async def get_contest_users(self, contest_id: int) -> list[ContestUserSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(ContestUser).where(ContestUser.contest_id == contest_id))

        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for user in raw_res:
            res.append(ContestUserSchema.model_validate(user))

        self.logger.debug(
            f"contest={contest_id}: has {len(res)} users",
            extra=extra_params(contest_id=contest_id)
        )

        return res

    async def get_contest_user(self, contest_id: int, user_id: int):
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(ContestUser).where(ContestUser.contest_id == contest_id,
                                                                   ContestUser.user_id == user_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise ContestUserNotFound(f"contest_id={contest_id}, user_id={user_id}: "
                                      f"contest user not found in database.")

        self.logger.debug(
            f"contest_id={contest_id}: user {user_id} is found",
            extra=extra_params(user_id=user_id, contest_id=contest_id)
        )

        return ContestUserSchema.model_validate(res)

    async def add_contest_user(self, contest_id: int, user_id: int, full_name: str, username: str | None):
        new_user = ContestUserSchema(contest_id=contest_id,
                                     user_id=user_id,
                                     join_date=datetime.now().replace(tzinfo=None),
                                     is_won=False,
                                     full_name=full_name,
                                     username=username)
        async with self.engine.begin() as conn:
            try:
                await conn.execute(insert(ContestUser).values(
                    **new_user.model_dump(by_alias=True))
                )
            except IntegrityError:
                raise InstanceAlreadyExists(f"user with {user_id} already exists in contest {contest_id} list")
        await self.engine.dispose()

        self.logger.debug(
            f"contest_id={contest_id}: user {user_id} is added to contest members db",
            extra=extra_params(user_id=user_id, contest_id=contest_id)
        )

    async def update_contest_user(self, updated_user: ContestUserSchema):
        async with self.engine.begin() as conn:
            await conn.execute(update(ContestUser).where(ContestUser.contest_id == updated_user.contest_id,
                                                         ContestUser.user_id == updated_user.user_id).
                               values(**updated_user.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"contest_id={updated_user.contest_id}: contest user {updated_user.user_id} is updated",
            extra=extra_params(contest_id=updated_user.contest_id, user_id=updated_user.user_id)
        )
