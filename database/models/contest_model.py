from datetime import datetime

from pydantic import BaseModel, Field, validate_call, ConfigDict

from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, update, Boolean, DateTime, String
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot
from database.exceptions.exceptions import KwargsException
from database.models.post_message_model import PostMessage

from logs.config import extra_params


class ContestNotFoundError(KwargsException):
    """Raised when provided contest not found in database"""


class ContestUserNotFoundError(KwargsException):
    """Raised when provided contest user not found in database"""


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
        """
        Returns all contests belonging to Bot
        """
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
        """
        Returns not finished  contest found by post_message_id
        :param post_message_id: belonging to contest

        :raises ContestNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Contest).where(Contest.post_message_id == post_message_id, Contest.is_finished == False)  # noqa
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ContestNotFoundError(post_message_id=post_message_id)

        res = ContestSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: found contest: {res}",
            extra=extra_params(bot_id=res.bot_id, contest_id=res.contest_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_contest_by_bot_id(self, bot_id: int) -> ContestSchema:
        """
        Returns not finished contest found by bot_id
        :param bot_id: belonging to contest

        :raises ContestNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Contest).where(Contest.bot_id == bot_id, Contest.is_finished == False)  # noqa
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ContestNotFoundError(bot_id=bot_id)

        res = ContestSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: found contest: {res}",
            extra=extra_params(bot_id=res.bot_id, contest_id=res.contest_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_contest_by_contest_id(self, contest_id: int) -> ContestSchema:
        """
        Returns contest found by contest_id
        :param contest_id: belonging to contest

        :raises ContestNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Contest).where(Contest.contest_id == contest_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ContestNotFoundError(contest_id=contest_id)

        res = ContestSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: found contest: {res}",
            extra=extra_params(bot_id=res.bot_id, contest_id=res.contest_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_contest(self, new_contest: ContestSchemaWithoutId) -> int:
        """
        :raises IntegrityError:
        """
        async with self.engine.begin() as conn:
            contest_id = (
                await conn.execute(insert(Contest).values(new_contest.model_dump()))
            ).inserted_primary_key[0]

        self.logger.debug(
            f"bot_id={new_contest.bot_id}: added contest {new_contest}",
            extra=extra_params(bot_id=new_contest.bot_id, contest_id=contest_id)
        )

        return contest_id

    @validate_call(validate_return=True)
    async def update_contest(self, updated_contest: ContestSchema) -> None:
        """
        Updates Contest in database
        """
        async with self.engine.begin() as conn:
            await conn.execute(update(Contest).where(Contest.contest_id == updated_contest.contest_id).
                               values(**updated_contest.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"contest_id={updated_contest.contest_id}: updated contest {updated_contest}",
            extra=extra_params(contest_id=updated_contest.contest_id, bot_id=updated_contest.bot_id)
        )

    @validate_call(validate_return=True)
    async def delete_contest(self, contest: ContestSchema) -> None:
        """
        Deletes Contest from database
        """
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(Contest).where(
                    Contest.contest_id == contest.contest_id
                )
            )

        self.logger.debug(
            f"bot_id={contest.bot_id}: deleted contest {contest}",
            extra=extra_params(bot_id=contest.bot_id,
                               contest_id=contest.contest_id)
        )

    @validate_call(validate_return=True)
    async def get_contest_users(self, contest_id: int) -> list[ContestUserSchema]:
        """
        Returns all contest users belonging to contest
        """
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

    @validate_call(validate_return=True)
    async def get_contest_user(self, contest_id: int, user_id: int):
        """
        Returns contest user found by contest_id and user_id

        :raises ContestUserNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(ContestUser).where(ContestUser.contest_id == contest_id,
                                                                   ContestUser.user_id == user_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise ContestUserNotFoundError(user_id=user_id, contest_id=contest_id)

        res = ContestUserSchema.model_validate(res)

        self.logger.debug(
            f"contest_id={contest_id}: found user {user_id}",
            extra=extra_params(user_id=user_id, contest_id=contest_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_contest_user(self, contest_id: int, user_id: int, full_name: str, username: str | None):
        """
        :raises IntegrityError:
        """
        new_user = ContestUserSchema(contest_id=contest_id,
                                     user_id=user_id,
                                     join_date=datetime.now().replace(tzinfo=None),
                                     is_won=False,
                                     full_name=full_name,
                                     username=username)
        async with self.engine.begin() as conn:
            await conn.execute(insert(ContestUser).values(
                **new_user.model_dump(by_alias=True))
            )
        await self.engine.dispose()

        self.logger.debug(
            f"contest_id={contest_id}: joined user {new_user}",
            extra=extra_params(user_id=user_id, contest_id=contest_id)
        )

    @validate_call(validate_return=True)
    async def update_contest_user(self, updated_user: ContestUserSchema):
        """
        Updates ContestUser in database
        """
        async with self.engine.begin() as conn:
            await conn.execute(update(ContestUser).where(ContestUser.contest_id == updated_user.contest_id,
                                                         ContestUser.user_id == updated_user.user_id).
                               values(**updated_user.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"contest_id={updated_user.contest_id}: updated contest {updated_user}",
            extra=extra_params(contest_id=updated_user.contest_id, user_id=updated_user.user_id)
        )
