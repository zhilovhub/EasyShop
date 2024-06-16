from datetime import datetime

from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, update, DateTime, desc
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao
from logs.config import extra_params
from database.models.channel_model import Channel


class CustomAd(Base):
    __tablename__ = "custom_ad"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    channel_id = Column(ForeignKey(Channel.channel_id, ondelete="CASCADE"))
    message_id = Column(BigInteger)
    time_until = Column(DateTime)


class CustomAdSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: int
    message_id: int
    time_until: datetime


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
