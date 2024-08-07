import json
from datetime import datetime

from aiogram import F
from aiogram.types import Message
from aiogram.handlers import PreCheckoutQueryHandler

from common_utils.keyboards.order_manage_keyboards import InlineOrderStatusesKeyboard, InlineOrderCustomBotKeyboard

from custom_bots.multibot import PREV_ORDER_MSGS, main_bot

from database.models.order_model import OrderStatusValues
from database.models.payment_model import PaymentSchemaWithoutId
from database.config import pay_db, bot_db, order_db, product_db

from common_utils.message_texts import MessageTexts as CommonMessageTexts

from typing import Any

from custom_bots.handlers.routers import payment_router

from logs.config import custom_bot_logger, extra_params


@payment_router.pre_checkout_query()
class PreCheckHandler(PreCheckoutQueryHandler):
    async def handle(self) -> Any:
        bot_id = "cant get"
        from_user = self.event.from_user
        try:
            custom_bot = await bot_db.get_bot_by_token(self.bot.token)
            bot_id = custom_bot.bot_id
            payload = self.event.invoice_payload
            extra_data = self.event.order_info
            custom_bot_logger.info(f"new custom bot payment pre checkout with payload : payload={payload} "
                                   f"and extra data : data=[{extra_data}]",
                                   extra=extra_params(user_id=from_user.id,
                                                      bot_id=bot_id))
            if "TEST" not in payload:
                payload_params = json.loads(payload)
                order = await order_db.get_order(payload_params['order_id'])
                order.status = OrderStatusValues.PROCESSING
                msg_id_data = PREV_ORDER_MSGS.get_data()

                products = [
                    (await product_db.get_product(
                        int(product_id)), product_item.amount, product_item.used_extra_options
                     ) for product_id, product_item in order.items.items()
                ]

                for item_id, item in order.items.items():
                    product = await product_db.get_product(item_id)
                    product.count += item.amount
                    await product_db.update_product(product)

                text = await CommonMessageTexts.generate_order_notification_text(
                    order=order,
                    products=products,
                    username="@" + from_user.username if from_user.username else from_user.full_name,
                    is_admin=True
                )

                user_text = await CommonMessageTexts.generate_order_notification_text(
                    order=order,
                    products=products,
                    username="@" + from_user.username if from_user.username else from_user.full_name,
                    is_admin=False
                )

                await main_bot.edit_message_text(
                    **text, chat_id=msg_id_data[order.id][0], message_id=msg_id_data[order.id][1],
                    reply_markup=InlineOrderStatusesKeyboard.get_keyboard(
                        order.id, msg_id_data[order.id][2], from_user.id, current_status=order.status
                    )
                )
                await main_bot.send_message(
                    chat_id=msg_id_data[order.id][0],
                    text=f"Новый статус заказа <b>#{order.id}</b>\n<b>{order.translate_order_status()}</b>")

                await self.bot.edit_message_text(
                    chat_id=self.from_user.id,
                    message_id=msg_id_data[order.id][2],
                    reply_markup=InlineOrderCustomBotKeyboard.get_keyboard(order.id),
                    **user_text
                )

                await order_db.update_order(order)

            await self.update.pre_checkout_query.answer(ok=True)
        except Exception:
            custom_bot_logger.error(f"unhandled error while processing payment for user {from_user.id}"
                                    f" in bot {bot_id}",
                                    exc_info=True, extra=extra_params(user_id=from_user.id,
                                                                      bot_id=bot_id))
            await self.update.pre_checkout_query.answer(
                ok=False,
                error_message="Произошла неопознанная ошибка, мы уже работаем над этим."
            )
            raise


@payment_router.message(F.successful_payment)
async def process_successfully_payment(message: Message):
    payment = message.successful_payment
    payload = payment.invoice_payload
    custom_bot = await bot_db.get_bot_by_token(message.bot.token)
    if "TEST" in payload:
        custom_bot_logger.debug("new test success payment, skipping payment database object creation")
        pay_id = "TEST"
    else:
        now = datetime.now()
        db_payment = PaymentSchemaWithoutId(
            from_user=message.from_user.id,
            amount=payment.total_amount,
            status="success",
            created_at=now,
            last_update=now,
            from_main_bot=False,
            custom_bot_id=custom_bot.bot_id
        )
        pay_id = await pay_db.add_payment(db_payment)

    await message.answer(f"✅ Оплата прошла успешно. [payment_id: {pay_id}]")
