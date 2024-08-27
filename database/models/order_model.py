from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validate_call, ConfigDict, ValidationError

from sqlalchemy import BigInteger, Column, String, TypeDecorator, Unicode, Dialect, DateTime, JSON, ForeignKey
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from common_utils.non_actual_data_fix import non_actual_data_fix
from database.enums import UserLanguageValues

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot
from database.exceptions.exceptions import KwargsException

from logs.config import extra_params


class OrderStatusValues(Enum):
    BACKLOG = "backlog"
    WAITING_PAYMENT = "waiting payment"
    CANCELLED = "cancelled"
    PROCESSING = "processing"
    FINISHED = "finished"


class OrderStatus(TypeDecorator):  # noqa
    """Class to convert Enum values to db values (and reverse)"""

    impl = Unicode
    cache_ok = True

    def process_bind_param(self, value: Optional[OrderStatusValues], dialect: Dialect) -> String:  # noqa
        return value.value

    def process_result_value(self, value: Optional[String], dialect: Dialect) -> Optional[OrderStatusValues]:  # noqa
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


class OrderNotFoundError(KwargsException):
    """Raised when provided product not found in database"""


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(13), primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"))
    items = Column(JSON, default="{}")
    from_user = Column(BigInteger, nullable=False)  # TODO make it Foreign
    order_options = Column(JSON)
    status = Column(OrderStatus)
    payment_method = Column(String, nullable=False)
    ordered_at = Column(DateTime, default=datetime.now())
    time = Column(String)


class OrderItemExtraOption(BaseModel):
    name: str
    selected_variant: str
    price: int = 0


class OrderItem(BaseModel):
    # product_id: int
    amount: int
    used_extra_options: list[OrderItemExtraOption] = []


class OrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(max_length=12, frozen=True, alias="order_id")
    bot_id: int
    items: dict[int, OrderItem] = Field(
        default={
            101: OrderItem(
                amount=2,
                used_extra_options=[
                    OrderItemExtraOption(
                        name="размер",
                        selected_variant="42",
                    )
                ],
            )
        }
    )
    from_user: int
    payment_method: str | None = None
    status: OrderStatusValues
    ordered_at: datetime
    order_options: dict
    time: str | None = None

    def translate_order_status(self, lang: UserLanguageValues = UserLanguageValues.RUSSIAN) -> str:
        status_dict = {
            OrderStatusValues.BACKLOG.value: {
                UserLanguageValues.RUSSIAN.value: "⏳ В обработке",
                UserLanguageValues.ENGLISH.value: "⏳ Backlog",
                UserLanguageValues.HEBREW.value: "⏳ בעיבוד",
            },
            OrderStatusValues.WAITING_PAYMENT.value: {
                UserLanguageValues.RUSSIAN.value: "💳 Ожидает оплаты",
                UserLanguageValues.ENGLISH.value: "💳 Waiting for payment",
                UserLanguageValues.HEBREW.value: "💳 מצפה לתשלום",
            },
            OrderStatusValues.CANCELLED.value: {
                UserLanguageValues.RUSSIAN.value: "❌ Отменен",
                UserLanguageValues.ENGLISH.value: "❌ Canceled",
                UserLanguageValues.HEBREW.value: "❌ בוטל",
            },
            OrderStatusValues.PROCESSING.value: {
                UserLanguageValues.RUSSIAN.value: "🚛 Выполняется",
                UserLanguageValues.ENGLISH.value: "🚛 In progress",
                UserLanguageValues.HEBREW.value: "🚛 מנהל",
            },
            OrderStatusValues.FINISHED.value: {
                UserLanguageValues.RUSSIAN.value: "✅ Завершен",
                UserLanguageValues.ENGLISH.value: "✅ Completed",
                UserLanguageValues.HEBREW.value: "✅ הושלם",
            },
            "unknown": {
                UserLanguageValues.RUSSIAN.value: "❓ Неизвестен",
                UserLanguageValues.ENGLISH.value: "❓ Unknown",
                UserLanguageValues.HEBREW.value: "❓ לא ידוע",
            },
        }
        lang = lang.value
        match self.status:
            case OrderStatusValues.BACKLOG:
                return status_dict[OrderStatusValues.BACKLOG.value][lang]
            case OrderStatusValues.WAITING_PAYMENT:
                return status_dict[OrderStatusValues.WAITING_PAYMENT.value][lang]
            case OrderStatusValues.CANCELLED:
                return status_dict[OrderStatusValues.CANCELLED.value][lang]
            case OrderStatusValues.PROCESSING:
                return status_dict[OrderStatusValues.PROCESSING.value][lang]
            case OrderStatusValues.FINISHED:
                return status_dict[OrderStatusValues.FINISHED.value][lang]
            case _:
                return status_dict["unknown"][lang]


class OrderDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_orders(self, bot_id: int) -> list[OrderSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Order).where(Order.bot_id == bot_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for order in raw_res:
            res.append(OrderSchema.model_validate(order))

        self.logger.debug(f"bot_id={bot_id}: has {len(res)} orders", extra=extra_params(bot_id=bot_id))

        return res

    @validate_call(validate_return=True)
    async def get_order(self, order_id: str) -> OrderSchema:
        """
        :raises OrderNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Order).where(Order.id == order_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise OrderNotFoundError(order_id=order_id)

        try:
            res = OrderSchema.model_validate(raw_res)
        except ValidationError as e:
            res = OrderSchema.model_validate(non_actual_data_fix(raw_res, e))

        self.logger.debug(
            f"bot_id={res.bot_id}: found order {res}", extra=extra_params(order_id=order_id, bot_id=res.bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_order(self, new_order: OrderSchema):
        """
        :raises IntegrityError:
        """
        async with self.engine.begin() as conn:
            await conn.execute(insert(Order).values(new_order.model_dump()))

        self.logger.debug(
            f"bot_id={new_order.bot_id}: added order {new_order}",
            extra=extra_params(order_id=new_order.id, bot_id=new_order.bot_id),
        )

    @validate_call(validate_return=True)
    async def update_order(self, updated_order: OrderSchema):
        await self.get_order(updated_order.id)
        async with self.engine.begin() as conn:
            await conn.execute(update(Order).where(Order.id == updated_order.id).values(updated_order.model_dump()))

        self.logger.debug(
            f"bot_id={updated_order.bot_id}: updated order {updated_order}",
            extra=extra_params(order_id=updated_order.id, bot_id=updated_order.bot_id),
        )

    @validate_call(validate_return=True)
    async def delete_order(self, order_id: str):
        await self.get_order(order_id)
        async with self.engine.begin() as conn:
            await conn.execute(delete(Order).where(Order.id == order_id))

        self.logger.debug(f"order_id={order_id}: deleted order {order_id}", extra=extra_params(order_id=order_id))
