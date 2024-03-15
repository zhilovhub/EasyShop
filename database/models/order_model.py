from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Column, String, TypeDecorator, Unicode, Dialect, DateTime, JSON, ForeignKey
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, validate_call, ConfigDict

from database.models import Base
from database.models.dao import Dao
from database.models.product_model import ProductSchema
from database.models.bot_model import Bot


class OrderStatusValues(Enum):
    BACKLOG = "backlog"
    WAITING_PAYMENT = "waiting payment"
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
            case OrderStatusValues.WAITING_PAYMENT.value:
                return OrderStatusValues.WAITING_PAYMENT
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
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"))
    products = Column(JSON)
    from_user = Column(BigInteger, nullable=False)  # TODO make it Foreign
    payment_method = Column(String, nullable=False)
    ordered_at = Column(DateTime, default=datetime.now())
    address = Column(String)
    status = Column(OrderStatus)
    comment = Column(String)


class OrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(max_length=12, frozen=True, alias="order_id")
    bot_id: int
    products: dict[int, int]
    from_user: int
    payment_method: str
    ordered_at: datetime
    address: str
    status: OrderStatusValues
    comment: str

    def translate_order_status(self) -> str:
        match self.status:
            case OrderStatusValues.BACKLOG:
                return "⏳ В обработке"
            case OrderStatusValues.WAITING_PAYMENT:
                return "💳 Ожидает оплаты"
            case OrderStatusValues.CANCELLED:
                return "❌ Отменен"
            case OrderStatusValues.PROCESSING:
                return "🚛 Выполняется"
            case OrderStatusValues.FINISHED:
                return "✅ Завершен"
            case _:
                return "❓ Неизвестен"

    def convert_to_notification_text(self, products: list[tuple[ProductSchema, int]], username: str = '@username', is_admin: bool = False) -> str:
        products_converted = []
        total_price = 0
        for ind, product_item in enumerate(products, start=1):
            products_converted.append(f"{ind}. {product_item[0].convert_to_notification_text(product_item[1])}")
            total_price += product_item[0].price * product_item[1]

        products_text = "\n".join(products_converted)

        return f"Ваш заказ <b>#{self.id}</b>\n\n" \
               f"Список товаров:\n\n" \
               f"{products_text}\n" \
               f"Итого: <b>{total_price}₽</b>\n\n" \
               f"Адрес: <b>{self.address}</b>\n" \
               f"Способ оплаты: <b>{self.payment_method}</b>\n" \
               f"Комментарий: <b>{self.comment}</b>\n\n" \
               f"Статус: <b>{self.translate_order_status()}</b>" if not is_admin \
            else f"Новый заказ <b>#{self.id}</b>\n" \
                 f"от пользователя " \
                 f"<b>{username}</b>\n\n" \
                 f"Список товаров:\n\n" \
                 f"{products_text}\n" \
                 f"Итого: <b>{total_price}₽</b>\n\n" \
                 f"Адрес: <b>{self.address}</b>\n" \
                 f"Способ оплаты: <b>{self.payment_method}</b>\n" \
                 f"Комментарий: <b>{self.comment}</b>\n\n" \
                 f"Статус: <b>{self.translate_order_status()}</b>"


class OrderDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call
    async def get_all_orders(self, bot_id: int) -> list[OrderSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Order).where(Order.bot_id == bot_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for order in raw_res:
            res.append(OrderSchema.model_validate(order))

        self.logger.info(f"get_all_orders method with bot_id: {bot_id} success")
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
    async def add_order(self, new_order: OrderSchema):
        async with self.engine.begin() as conn:
            await conn.execute(insert(Order).values(new_order.model_dump()))
        self.logger.info(f"successfully add order with id {new_order.id} to db.")

    @validate_call
    async def update_order(self, updated_order: OrderSchema):
        await self.get_order(updated_order.id)
        async with self.engine.begin() as conn:
            await conn.execute(update(Order).where(Order.id == updated_order.id).values(updated_order.model_dump()))
        self.logger.info(f"successfully update order with id {updated_order.id} at db.")

    @validate_call
    async def delete_order(self, order_id: str):
        await self.get_order(order_id)
        async with self.engine.begin() as conn:
            await conn.execute(delete(Order).where(Order.id == order_id))
        self.logger.info(f"deleted order with id {order_id}")
