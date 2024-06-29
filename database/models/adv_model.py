from datetime import datetime

from pydantic import BaseModel, Field, validate_call, ConfigDict

from sqlalchemy import BigInteger, Column, select, insert, DateTime, desc
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao

from logs.config import extra_params


class EmptyAdvTable(Exception):
    pass


class Adv(Base):
    __tablename__ = "adv"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    total_count = Column(BigInteger, default=0)
    total_unique_count = Column(BigInteger, default=0)

    time = Column(DateTime)


class AdvSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_count: int = 0
    total_unique_count: int = 0

    time: datetime


class AdvSchema(AdvSchemaWithoutId):
    id: int = Field(frozen=True)


class AdvDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_last_adv(self) -> AdvSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Adv).order_by(desc(Adv.id)).limit(1)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if raw_res is None:
            raise EmptyAdvTable

        res = AdvSchema.model_validate(raw_res)

        self.logger.debug(
            f"adv={res.id}: total_count = {res.total_count}, "
            f"total_unique_count = {res.total_unique_count}",
            extra=extra_params(adv_id=res.id)
        )

        return res

    @validate_call
    async def add_adv(self, new_schema: AdvSchemaWithoutId) -> None:
        new_schema.time = datetime.utcnow().replace(tzinfo=None)
        async with self.engine.begin() as conn:
            adv_id = (await conn.execute(insert(Adv).values(
                new_schema.model_dump(exclude={"id"}))
            )).inserted_primary_key[0]

        self.logger.debug(
            f"adv={adv_id}: new adv is created",
            extra=extra_params(adv_id=adv_id)
        )
