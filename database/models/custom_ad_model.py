from datetime import datetime

from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, update, DateTime, desc, String
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao
from logs.config import extra_params
from database.models.channel_model import Channel
from database.models.user_model import User


class CustomAdsNotFound(Exception):
    pass


class CustomAd(Base):
    __tablename__ = "custom_ad"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    channel_id = Column(ForeignKey(Channel.channel_id, ondelete="CASCADE"))
    by_user = Column(ForeignKey(User.user_id, ondelete="CASCADE"))
    message_id = Column(BigInteger)
    time_until = Column(DateTime)
    status = Column(String(length=15))
    finish_job_id = Column(String)


class CustomAdSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: int
    message_id: int
    by_user: int
    time_until: datetime
    status: str = Field(max_length=15)
    finish_job_id: str


class CustomAdSchema(CustomAdSchemaWithoutId):
    id: int = Field(frozen=True)


class CustomAdDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call
    async def add_ad(self, new_ad: CustomAdSchemaWithoutId) -> int:
        async with self.engine.begin() as conn:
            ad_id = (await conn.execute(insert(CustomAd).values(new_ad.model_dump()))).inserted_primary_key[0]

        self.logger.debug(
            f"custom ad={ad_id}: new adv is created",
            extra=extra_params(custom_ad_id=ad_id)
        )
        return ad_id

    async def get_channel_last_custom_ad(self, channel_id: int):
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(CustomAd).order_by(desc(CustomAd.id)).limit(1)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if raw_res is None:
            raise CustomAdsNotFound

        res = CustomAdSchema.model_validate(raw_res)
        self.logger.debug(
            f"custom_ad={res.id}", extra=extra_params(custom_ad_id=res.id)
        )
        return res

    async def update_custom_ad(self, updated_ad: CustomAdSchema):
        async with self.engine.begin() as conn:
            await conn.execute(update(CustomAd).where(CustomAd.id == updated_ad.id).
                               values(**updated_ad.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.debug(
            f"custom_ad_id={updated_ad.id}: custom ad {updated_ad.id} is updated",
            extra=extra_params(custom_ad_id=updated_ad.id)
        )

    async def del_ad(self, ad: CustomAdSchema) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(CustomAd).where(
                    CustomAd.id == ad.id
                )
            )

        self.logger.debug(
            f"custom_ad_id={ad.id}: custom ad {ad.id} is deleted",
            extra=extra_params(custom_ad_id=ad.id)
        )
