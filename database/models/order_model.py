from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Column, String, TIMESTAMP, ForeignKey, TypeDecorator, Unicode, Dialect
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field

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


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True)
    product_id = Column(ForeignKey(Product.id))
    from_user = Column(ForeignKey(CustomBotUser.user_id))
    ordered_at = Column(TIMESTAMP, default=datetime.utcnow)
    address = Column(String)
    status = Column(OrderStatus)


class OrderSchema(BaseModel):
    id: int
    product_id: int
    from_user: int
    ordered_at: datetime
    address: str
    status: OrderStatusValues


class OrderDao(Dao):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)
