from datetime import datetime

from sqlalchemy import BigInteger, Column, String, DateTime, ForeignKey
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict, field_validator

from database.models import Base
from database.models.dao import Dao

from bot.exceptions.exceptions import *

from database.models.user_model import User


class PaymentNotFound(Exception):
    """Raised when provided user not found in database"""
    pass


PAYMENT_STATUSES = ("waiting_payment", "success", "error", "refund")


class NotInPaymentStatusesList(ValueError):
    """Error when value of user status not in values list"""
    pass


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(BigInteger, primary_key=True)
    from_user = Column(ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False)
    amount = Column(BigInteger, )
    status = Column(String(55), nullable=False)
    created_at = Column(DateTime, nullable=False)
    last_update = Column(DateTime, nullable=False)

    # Telegram payments system
    # telegram_payment_charge_id = Column(String, nullable=False)
    # provider_payment_charge_id = Column(String, nullable=False)
    # invoice_payload = Column(String)
    # shipping_option_id = Column(String)


class PaymentSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_user: int
    amount: int
    status: str = Field(max_length=55)
    created_at: datetime
    last_update: datetime

    # Telegram payments system
    # telegram_payment_charge_id: str
    # provider_payment_charge_id: str
    # invoice_payload: Optional | str
    # shipping_option_id: Optional | str

    @field_validator("status")
    def validate_request_status(cls, value: str):
        if value.lower() not in PAYMENT_STATUSES:
            raise NotInPaymentStatusesList(f"status value must be one of {', '.join(PAYMENT_STATUSES)}")
        return value.lower()


class PaymentSchema(PaymentSchemaWithoutId):
    id: int = Field(alias="payment_id", frozen=True)


class PaymentDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)
        
    async def get_all_payments(self) -> list[PaymentSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Payment))
        await self.engine.dispose()
        
        raw_res = raw_res.fetchall()
        res = []
        for user in raw_res:
            res.append(PaymentSchema.model_validate(user))

        self.logger.info(f"get_all_payments method success.")
        return res
    
    async def get_payment(self, payment_id: int) -> PaymentSchema:
        if not isinstance(payment_id, int):
            raise InvalidParameterFormat("payment_id must be type of int.")
        
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Payment).where(Payment.payment_id == payment_id))
        await self.engine.dispose()
        
        res = raw_res.fetchone()
        if res is None:
            raise PaymentNotFound(f"id {payment_id} not found in database.")

        self.logger.info(f"get_payment method with user_id: {payment_id} success.")
        return PaymentSchema.model_validate(res)

    async def add_payment(self, payment: PaymentSchemaWithoutId) -> None:
        if not isinstance(payment, PaymentSchemaWithoutId):
            raise InvalidParameterFormat("payment must be type of database.PaymentSchema.")

        # try:
        #     await self.get_payment(payment_id=payment.id)
        #     raise InstanceAlreadyExists(f"payment with {payment.id} already exists in db.")
        # except PaymentNotFound:
        async with self.engine.begin() as conn:
            payment_id = (await conn.execute(insert(Payment).values(**payment.model_dump(by_alias=True)))).inserted_primary_key[0]
        await self.engine.dispose()

        self.logger.info(f"successfully add payment with id {payment_id} to db.")

    async def update_payment(self, updated_payment: PaymentSchema) -> None:
        if not isinstance(updated_payment, PaymentSchema):
            raise InvalidParameterFormat("updated_payment must be type of database.PaymentSchema.")

        updated_payment.last_update = datetime.now()

        async with self.engine.begin() as conn:
            await conn.execute(update(User).where(Payment.payment_id == updated_payment.id).
                               values(**updated_payment.model_dump(by_alias=True)))
        await self.engine.dispose()

        self.logger.info(f"successfully update payment with id {updated_payment.id} in db.")
