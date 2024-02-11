from datetime import datetime
from enum import Enum
from typing import Optional
import string
import random

from sqlalchemy import BigInteger, Column, String, ForeignKey, TypeDecorator, Unicode, Dialect, ARRAY, DateTime
from sqlalchemy import select, update, delete, insert, and_
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, validate_call

from database.models import Base
from database.models.dao import Dao
from database.models.product_model import Product
from database.models.custom_bot_user_model import CustomBotUser


class OrderStatusValues(Enum):
    BACKLOG = "backlog"
    CANCELLED = "cancelled"
    PROCESSING = "processing"
    FINISHED = "finished"


class OrderStatus(TypeDecorator):
    impl = Unicode
    cache_ok = True

    def process_bind_param(self, value: Optional[OrderStatusValues], dialect: Dialect) -> String:
        return value.value

    def process_result_value(self, value: Optional[String], dialect: Dialect) -> Optional[OrderStatusValues]:
        match value:
            case OrderStatusValues.BACKLOG.value:
                return OrderStatusValues.BACKLOG
            case OrderStatusValues.CANCELLED.value:
                return OrderStatusValues.CANCELLED
            case OrderStatusValues.PROCESSING.value:
                return OrderStatusValues.PROCESSING
            case OrderStatusValues.FINISHED.value:
                return OrderStatusValues.FINISHED


class OrderNotFound(Exception):
    """Raised when provided product not found in database"""
    pass


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(13), primary_key=True)
    bot_token = Column(String(46))
    products_id = Column(ARRAY(BigInteger))
    from_user = Column(ForeignKey(CustomBotUser.user_id))
    ordered_at = Column(DateTime, default=datetime.now())
    address = Column(String)
    status = Column(OrderStatus)


class OrderWithoutId(BaseModel):
    bot_token: str = Field(max_length=46, min_length=46, frozen=True)
    products_id: list[int]
    from_user: int
    ordered_at: datetime
    address: str
    status: OrderStatusValues


class OrderSchema(OrderWithoutId):
    id: str = Field(max_length=12, frozen=True)


class OrderDao(Dao):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)

    @validate_call
    async def get_all_orders(self, bot_token: str) -> list[OrderSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Order).where(Order.bot_token == bot_token))
        await self.engine.dispose()
        raw_res = raw_res.fetchall()
        res = []
        for order in raw_res:
            res.append(OrderSchema.model_validate(order))
        return res

    @validate_call
    async def get_order(self, bot_token: str, order_id: str) -> OrderSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Order).where(and_(Order.bot_token == bot_token,
                                                                  Order.id == order_id)))
        await self.engine.dispose()
        raw_res = raw_res.fetchall()
        if not raw_res:
            raise OrderNotFound
        res = OrderSchema.model_validate(raw_res)
        return res

    @validate_call
    async def add_order(self, new_order: OrderWithoutId) -> OrderSchema:
        s = string.digits + string.ascii_letters
        day_id = ''.join(random.sample(s, 6))
        try:
            await self.get_order(new_order.bot_token, )
            return await self.add_order(new_order)
        except OrderNotFound:
            date = new_order.ordered_at.strftime("%d%m%y")
            order = OrderSchema(**new_order.model_dump(), id=f"{date}_{day_id}")
        async with self.engine.begin() as conn:
            await conn.execute(insert(Order).values(order.model_dump()))
        return order

    @validate_call
    async def update_order(self, updated_order: OrderSchema):
        old_order = await self.get_order(updated_order.bot_token, updated_order.id)
        async with self.engine.begin() as conn:
            await conn.execute(update(Order).where(and_(Order.bot_token == updated_order.bot_token,
                                                        Order.id == updated_order.id))
                               .values(updated_order.model_dump()))

    @validate_call
    async def delete_order(self, bot_token: str, order_id: str):
        order = await self.get_order(bot_token, order_id)
        async with self.engine.begin() as conn:
            await conn.execute(delete(Order).where(and_(Order.bot_token == bot_token, Order.id == order_id)))
