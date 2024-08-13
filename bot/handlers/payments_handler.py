from datetime import datetime

from aiogram import F
from aiogram.types import Message
from aiogram.handlers import PreCheckoutQueryHandler

from database.config import pay_db
from database.models.payment_model import PaymentSchemaWithoutId

from typing import Any

from bot.handlers.routers import payment_router

from logs.config import logger, extra_params


@payment_router.pre_checkout_query()
class PreCheckHandler(PreCheckoutQueryHandler):
    async def handle(self) -> Any:
        try:
            # TODO here all logic (for our subscription by tg provider or stars)
            payload = self.event.invoice_payload
            extra_data = self.event.order_info
            logger.info(
                f"new main bot payment pre checkout with payload : payload={payload} "
                f"and extra data : data=[{extra_data}]",
                extra=extra_params(user_id=self.event.from_user.id),
            )
            await self.update.pre_checkout_query.answer(ok=True)
        except Exception:
            logger.error(
                f"unhandled error while processing payment for user {self.event.from_user.id}",
                exc_info=True,
                extra=extra_params(user_id=self.event.from_user.id),
            )
            await self.update.pre_checkout_query.answer(
                ok=False, error_message="Произошла неопознанная ошибка, мы уже работаем над этим."
            )
            raise


@payment_router.message(F.successful_payment)
async def process_successfully_payment(message: Message):
    payment = message.successful_payment
    payload = payment.invoice_payload
    if "TEST" in payload:
        logger.debug("new test success payment, skipping payment database object creation")
        pay_id = "TEST"
        await message.answer(
            "Введенные данные при тестовой оплате:"
            f"\n\nИмя: {payment.order_info.name}"
            f"\n\nТелефон: {payment.order_info.phone_number}"
            f"\n\nПочта: {payment.order_info.email}"
            f"\n\nАдрес доставки: {payment.order_info.shipping_address}"
        )
    else:
        # For future payment for our subscription in main bot
        now = datetime.now()
        db_payment = PaymentSchemaWithoutId(
            from_user=message.from_user.id,
            amount=payment.total_amount,
            status="success",
            created_at=now,
            last_update=now,
            from_main_bot=True,
        )
        pay_id = await pay_db.add_payment(db_payment)

        # TODO notify admins about new payment (for our subscription by tg provider or stars)

    await message.answer(f"✅ Оплата прошла успешно. [payment_id: {pay_id}]")
