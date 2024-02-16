from datetime import datetime
from enum import Enum
from typing import Optional
import string
import random

from sqlalchemy import BigInteger, Column, String, TypeDecorator, Unicode, Dialect, ARRAY, DateTime
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, validate_call, ConfigDict

from database.models import Base
from database.models.dao import Dao
from database.models.product_model import ProductSchema


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
    from_user = Column(BigInteger, nullable=False)  # TODO make it Foreign
    ordered_at = Column(DateTime, default=datetime.now())
    address = Column(String)
    status = Column(OrderStatus)


class OrderWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_token: str = Field(max_length=46, min_length=46, frozen=True)
    products_id: list[int]
    from_user: int
    ordered_at: datetime
    address: str
    status: OrderStatusValues


class OrderSchema(OrderWithoutId):
    id: str = Field(max_length=12, frozen=True)

    def convert_to_notification_text(self, products: list[ProductSchema], username: str, is_admin: bool) -> str:
        products_converted = []
        total_price = 0
        for ind, product in enumerate(products, start=1):
            products_converted.append(f"{ind}. {product.convert_to_notification_text()}")
            total_price += product.price

        products_text = "\n".join(products_converted)

        return f"Твой заказ <b>#{self.id}</b>\n\n" \
               f"Список товаров:\n\n" \
               f"{products_text}\n\n" \
               f"Итого: <b>{total_price}₽</b>" if not is_admin \
            else f"Новый заказ <b>#{self.id}</b>\n" \
                 f"от пользователя " \
                 f"<b>{username}</b>\n\n" \
                 f"Список товаров:\n\n" \
                 f"{products_text}\n\n" \
                 f"Итого: <b>{total_price}₽</b>"


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
    async def get_order(self, order_id: str) -> OrderSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Order).where(Order.id == order_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise OrderNotFound

        res = OrderSchema.model_validate(raw_res)
        return res

    @validate_call
    async def add_order(self, new_order: OrderWithoutId) -> OrderSchema:
        date = new_order.ordered_at.strftime("%d%m%y")
        random_string = ''.join(random.sample(string.digits + string.ascii_letters, 5))
        order = OrderSchema(**new_order.model_dump(), id=f"{date}_{random_string}")

        async with self.engine.begin() as conn:
            await conn.execute(insert(Order).values(order.model_dump()))

        return order

    @validate_call
    async def update_order(self, updated_order: OrderSchema):
        await self.get_order(updated_order.id)
        async with self.engine.begin() as conn:
            await conn.execute(update(Order).where(Order.id == updated_order.id).values(updated_order.model_dump()))

    @validate_call
    async def delete_order(self, order_id: str):
        await self.get_order(order_id)
        async with self.engine.begin() as conn:
            await conn.execute(delete(Order).where(Order.id == order_id))
