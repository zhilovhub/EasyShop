from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, validate_call

from sqlalchemy import Column, BigInteger, Dialect, String, Boolean, Integer, TypeDecorator, Unicode, \
    select, ForeignKey, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from database.exceptions.exceptions import KwargsException

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot

from logs.config import extra_params

from enum import Enum


class OrderOptionNotFoundError(KwargsException):
    """Raised when provided order option not found in database"""


class UnknownOrderOptionType(KwargsException):
    """Raised when provided order option type is not expected"""


class OrderOptionTypeValues(Enum):
    TEXT = "text"
    CHOOSE = "choose"


class OrderOptionType(TypeDecorator):  # noqa
    """Class to convert Enum values to db values (and reverse)"""
    impl = Unicode
    cache_ok = True

    def process_bind_param(self, value: Optional[OrderOptionTypeValues], dialect: Dialect) -> String:
        return value.value

    def process_result_value(self, value: Optional[String], dialect: Dialect) -> Optional[OrderOptionTypeValues]:
        match value:
            case OrderOptionTypeValues.TEXT.value:
                return OrderOptionTypeValues.TEXT
            case OrderOptionTypeValues.CHOOSE.value:
                return OrderOptionTypeValues.CHOOSE


class OrderOption(Base):
    __tablename__ = "order_options"

    id = Column(BigInteger, primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), nullable=False)
    option_name = Column(String, nullable=False)
    hint = Column(String, default="Введите значение")
    required = Column(Boolean, nullable=False, default=False)
    emoji = Column(String, nullable=False)
    position_index = Column(Integer, nullable=False)
    option_type = Column(OrderOptionType, nullable=False)


class OrderOptionSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)
    option_name: str
    hint: str = "Введите значение"
    required: bool = False
    emoji: str = "🔷"
    position_index: int
    option_type: OrderOptionTypeValues = OrderOptionTypeValues.TEXT


class OrderOptionSchema(OrderOptionSchemaWithoutId):
    id: int = Field(frozen=True)


class OrderOptionDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_order_options(self, bot_id: int) -> list[OrderOptionSchema]:
        """
        :param bot_id: bot_id from search
        :return: list of OrderOptionSchema
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(OrderOption).where(OrderOption.bot_id == bot_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for order_option in raw_res:
            res.append(OrderOptionSchema.model_validate(order_option))

        self.logger.debug(
            f"bot_id={bot_id}: has {len(res)} order options",
            extra=extra_params(bot_id=bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_order_option(self, order_option_id: int) -> OrderOptionSchema:
        """
        :param order_option_id: order_option_id
        :return: OrderOptionSchema

        :raises OrderOptionNotFoundError: no order option in db
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(OrderOption).where(OrderOption.id == order_option_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise OrderOptionNotFoundError(order_option_id=order_option_id)

        res = OrderOptionSchema.model_validate(res)
        self.logger.debug(
            f"order_option_id={order_option_id}: found order option {res}",
            extra=extra_params(order_option_id=order_option_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_order_option(self, new_order_option: OrderOptionSchemaWithoutId) -> int:
        """
        Adds new order option
        """
        async with self.engine.begin() as conn:
            order_option_id = (
                await conn.execute(insert(OrderOption).values(new_order_option.model_dump()))
            ).inserted_primary_key[0]

        self.logger.debug(
            f"order_option_id={order_option_id}: new added order option {new_order_option}",
            extra=extra_params(bot_id=new_order_option.bot_id, order_option_id=order_option_id)
        )

        return order_option_id

    @validate_call(validate_return=True)
    async def update_order_option(self, updated_order_option: OrderOptionSchema) -> None:
        """
        Updates order option
        """
        bot_id, order_option_id = updated_order_option.bot_id, updated_order_option.id
        await self.get_order_option(order_option_id)

        async with self.engine.begin() as conn:
            await conn.execute(
                update(OrderOption).where(OrderOption.id == order_option_id).values(updated_order_option.model_dump())
            )

        self.logger.debug(
            f"order_option_id={order_option_id}: updated order option {updated_order_option}",
            extra=extra_params(bot_id=bot_id, order_option_id=order_option_id)
        )

    @validate_call
    async def delete_order_option(self, order_option_id: int) -> None:
        """
        Deletes the order option from database
        """
        async with self.engine.begin() as conn:
            await conn.execute(delete(OrderOption).where(OrderOption.id == order_option_id))

        self.logger.debug(
            f"order_option_id={order_option_id}: deleted order option {order_option_id}",
            extra=extra_params(order_option_id=order_option_id)
        )
