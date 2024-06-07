from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, update
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.bot_model import Bot
from database.models.dao import Dao
from logs.config import extra_params


class Adv(Base):
    __tablename__ = "adv"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    total_count = Column(BigInteger, default=0)
    total_unique_count = Column(BigInteger, default=0)


class AdvSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(frozen=True)

    total_count: int = 0
    total_unique_count: int = 0


class AdvDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_last_adv(self) -> AdvSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Adv).order_by(Adv.id).limit(1)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if raw_res is None:
            await self.add_new_adv()
            return await self.get_last_adv()

        res = AdvSchema.model_validate(raw_res)

        self.logger.debug(
            f"adv={AdvSchema.id}: total_count = {AdvSchema.total_count}, "
            f"total_unique_count = {AdvSchema.total_unique_count}",
            extra=extra_params(adv_id=AdvSchema.id)
        )

        return res

    @validate_call
    async def add_new_adv(self) -> None:
        async with self.engine.begin() as conn:
            adv_id = (await conn.execute(insert(Adv).values())).inserted_primary_key[0]

        self.logger.debug(
            f"adv={adv_id}: new adv is created",
            extra=extra_params(adv_id=adv_id)
        )

    @validate_call
    async def update_adv(self, updated_adv: AdvSchema) -> None:
        if not isinstance(updated_adv, AdvSchema):
            raise InvalidParameterFormat("updated_adv must be type of AdvSchema")

        async with self.engine.begin() as conn:
            await conn.execute(update(Adv).where(Adv.id == updated_adv.id).values(updated_adv.model_dump()))
        await self.engine.dispose()

        self.logger.debug(
            f"adv={updated_adv.id}: adv {updated_adv.id} is updated",
            extra=extra_params(adv_id=updated_adv.id)
        )
