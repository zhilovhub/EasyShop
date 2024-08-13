from datetime import datetime

from sqlalchemy import BigInteger, Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, ConfigDict, field_validator, validate_call

from database.models import Base
from database.models.dao import Dao
from database.models.user_model import User
from database.exceptions.exceptions import KwargsException


from logs.config import extra_params


class PaymentNotFoundError(KwargsException):
    """Raised when provided user not found in database"""


class NotInPaymentStatusesListError(ValueError):
    """Error when value of user status not in values list"""


PAYMENT_STATUSES = ("waiting_payment", "success", "error", "refund")


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(BigInteger, primary_key=True)
    from_user = Column(ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False)
    amount = Column(
        BigInteger,
    )
    status = Column(String(55), nullable=False)
    created_at = Column(DateTime, nullable=False)
    last_update = Column(DateTime, nullable=False)
    from_main_bot = Column(Boolean)
    custom_bot_id = Column(BigInteger)  # не добавляю ссылку на Bot.id чтобы платежи не удалялись при удалении бота


class PaymentSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_user: int
    amount: int
    status: str = Field(max_length=55)
    created_at: datetime
    last_update: datetime
    from_main_bot: bool = True
    custom_bot_id: int | None = None  # не добавляю ссылку на Bot.id чтобы платежи не удалялись при удалении бота

    @classmethod
    @field_validator("status")
    def validate_request_status(cls, value: str):
        """
        :raises NotInPaymentStatusesListError:
        """
        if value.lower() not in PAYMENT_STATUSES:
            raise NotInPaymentStatusesListError(f"status value must be one of {', '.join(PAYMENT_STATUSES)}")
        return value.lower()


class PaymentSchema(PaymentSchemaWithoutId):
    id: int = Field(alias="payment_id", frozen=True)


class PaymentDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_payments(self) -> list[PaymentSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Payment))
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for payment in raw_res:
            res.append(PaymentSchema.model_validate(payment))

        self.logger.debug(
            f"payments: there are {len(res)} payments",
        )

        return res

    @validate_call(validate_return=True)
    async def get_payment(self, payment_id: int) -> PaymentSchema:
        """
        :raises PaymentNotFoundError
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Payment).where(Payment.payment_id == payment_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise PaymentNotFoundError(payment_id=payment_id)

        res = PaymentSchema.model_validate(res)

        self.logger.debug(
            f"payment_id={payment_id}: found payment {res}",
            extra=extra_params(payment_id=payment_id, user_id=res.from_user),
        )

        return res

    @validate_call(validate_return=True)
    async def add_payment(self, payment: PaymentSchemaWithoutId) -> int:
        """
        :raises IntegrityError:
        """
        async with self.engine.begin() as conn:
            payment_id = (
                await conn.execute(insert(Payment).values(**payment.model_dump(by_alias=True)))
            ).inserted_primary_key[0]
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={payment.from_user}: added payment {payment_id} {payment}",
            extra=extra_params(payment_id=payment_id, user_id=payment.from_user),
        )

        return payment_id

    @validate_call(validate_return=True)
    async def update_payment(self, updated_payment: PaymentSchema) -> None:
        updated_payment.last_update = datetime.now()

        async with self.engine.begin() as conn:
            await conn.execute(
                update(User)
                .where(Payment.payment_id == updated_payment.id)
                .values(**updated_payment.model_dump(by_alias=True))
            )
        await self.engine.dispose()

        self.logger.debug(
            f"user_id={updated_payment.from_user}: updated payment {updated_payment}",
            extra=extra_params(payment_id=updated_payment.id, user_id=updated_payment.from_user),
        )
