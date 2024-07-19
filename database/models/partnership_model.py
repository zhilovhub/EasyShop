from datetime import datetime, timedelta

from pydantic import BaseModel, Field, validate_call, ConfigDict

from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, update, Boolean, DateTime, String,\
    Interval
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao
from database.exceptions import InvalidParameterFormat
from database.models.bot_model import Bot
from database.models.post_message_model import PostMessage

from logs.config import extra_params


class PartnershipNotFound(Exception):
    """Raised when provided partnership not found in database"""
    pass


class CriteriaNotFound(Exception):
    """Raised when provided criteria not found in database"""
    pass


class Criteria(Base):
    __tablename__ = "partnerships_criteria"
    criteria_id = Column(BigInteger, primary_key=True, unique=True)

    users_count = Column(BigInteger)
    time = Column(Interval)


class Partnership(Base):
    __tablename__ = "partnerships"
    partnership_id = Column(BigInteger, primary_key=True, unique=True)

    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"))
    post_message_id = Column(ForeignKey(PostMessage.post_message_id, ondelete="CASCADE"))

    price = Column(BigInteger)
    criteria_id = Column(ForeignKey(Criteria.criteria_id, ondelete="CASCADE"), nullable=False)

    start_date = Column(DateTime)
    is_finished = Column(Boolean)
    finish_date = Column(DateTime)
    finish_job_id = Column(String, nullable=True)


class CriteriaSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    users_count: int
    time: timedelta


class CriteriaSchema(BaseModel):
    criteria_id: int = Field(frozen=True)


class PartnershipSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)

    post_message_id: int = Field(frozen=True)

    price: int
    criteria_id: int = Field(frozen=True)

    start_date: datetime | None = None
    is_finished: bool = False
    finish_date: datetime | None = None
    finish_job_id: str | None = None


class PartnershipSchema(PartnershipSchemaWithoutId):
    partnership_id: int = Field(frozen=True)


class PartnershipDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_partnerships(self, bot_id: int) -> list[PartnershipSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Partnership).where(Partnership.bot_id == bot_id)  # noqa
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for contest in raw_res:
            res.append(PartnershipSchema.model_validate(contest))

        self.logger.debug(
            f"bot_id={bot_id}: has {len(res)} partnerships",
            extra=extra_params(bot_id=bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_partnership_by_post_message_id(self, post_message_id: int) -> PartnershipSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Partnership).where(Partnership.post_message_id == post_message_id,  # noqa
                                          Partnership.is_finished == False)  # noqa
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise PartnershipNotFound

        res = PartnershipSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: partnership is found: {res}",
            extra=extra_params(bot_id=res.bot_id, partnership_id=res.partnership_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_partnership_by_bot_id(self, bot_id: int) -> PartnershipSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Partnership).where(Partnership.bot_id == bot_id, Partnership.is_finished == False)  # noqa
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise PartnershipNotFound

        res = PartnershipSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: partnership is found: {res}",
            extra=extra_params(bot_id=res.bot_id, partnership_id=res.partnership_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_partnership_by_id(self, partnership_id: int) -> PartnershipSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Partnership).where(Partnership.partnership_id == partnership_id))  # noqa
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise PartnershipNotFound

        res = PartnershipSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: partnership is found: {res}",
            extra=extra_params(bot_id=res.bot_id, partnership_id=res.partnership_id)
        )

        return res

    @validate_call
    async def add_partnership(self, new_partnership: PartnershipSchemaWithoutId) -> int:
        if not isinstance(new_partnership, PartnershipSchemaWithoutId):
            raise InvalidParameterFormat(
                "new_partnership must be type of PartnershipSchemaWithoutId")

        async with self.engine.begin() as conn:
            partnership_id = (
                await conn.execute(insert(Partnership).values(new_partnership.model_dump()))
            ).inserted_primary_key[0]

        self.logger.debug(
            f"bot_id={new_partnership.bot_id}: partnership {partnership_id} is added",
            extra=extra_params(bot_id=new_partnership.bot_id, partnership_id=partnership_id)
        )

        return partnership_id

    @validate_call
    async def update_partnership(self, updated_partnership: PartnershipSchema) -> None:
        if not isinstance(updated_partnership, PartnershipSchema):
            raise InvalidParameterFormat(
                "updated_partnership must be type of PartnershipSchema")
        async with self.engine.begin() as conn:
            await conn.execute(update(Partnership).where(Partnership.contest_id == updated_partnership.contest_id).  # noqa
                               values(**updated_partnership.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"partnership_id={updated_partnership.partnership_id}: "
            f"partnership {updated_partnership.partnership_id} is updated",
            extra=extra_params(partnership_id=updated_partnership.partnership_id, bot_id=updated_partnership.bot_id)
        )

    @validate_call
    async def delete_partnership(self, partnership: PartnershipSchema) -> None:
        if not isinstance(partnership, PartnershipSchema):
            raise InvalidParameterFormat(
                "partnership must be type of PartnershipSchema")

        async with self.engine.begin() as conn:
            await conn.execute(
                delete(Partnership).where(
                    Partnership.partnership_id == partnership.partnership_id  # noqa
                )
            )

        self.logger.debug(
            f"bot_id={partnership.bot_id}: partnership {partnership.partnership_id} is deleted",
            extra=extra_params(bot_id=partnership.bot_id, partnership_id=partnership.partnership_id)
        )

    async def get_partnership_criteria(self, criteria_id: int) -> CriteriaSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Criteria).where(Criteria.criteria_id == criteria_id))  # noqa

        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise CriteriaNotFound

        res = CriteriaSchema.model_validate(raw_res)

        self.logger.debug(
            f"criteria_id={criteria_id}: {res}",
            extra=extra_params(criteria_id=criteria_id)
        )

        return res

    async def create_partnership_criteria(self, new_criteria: CriteriaSchemaWithoutId) -> int:
        async with self.engine.begin() as conn:
            criteria_id = await conn.execute(insert(Criteria).values(
                **new_criteria.model_dump(by_alias=True))
            ).inserted_primary_key[0]
        await self.engine.dispose()

        self.logger.debug(
            f"criteria_id={criteria_id}: criteria added to database",
            extra=extra_params(criteria_id=criteria_id)
        )

        return criteria_id

    async def update_partnership_criteria(self, updated_criteria: CriteriaSchema):
        async with self.engine.begin() as conn:
            await conn.execute(update(Criteria).where(Criteria.criteria_id == updated_criteria.criteria_id).  # noqa
                               values(**updated_criteria.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"criteria_id={updated_criteria.criteria_id}: criteria {updated_criteria.criteria_id} is updated",
            extra=extra_params(criteria_id=updated_criteria.criteria_id)
        )
