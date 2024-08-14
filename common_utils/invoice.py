import json

from database.config import bot_db, option_db, product_db

from database.models.order_model import OrderItem
from database.models.bot_model import BotPaymentTypeValues

from aiogram.types import LabeledPrice


from common_utils.config import main_telegram_bot_settings


async def create_invoice_params(
    bot_id: int,
    user_id: int,
    order_items: dict[int, OrderItem],
    order_id: str,
    photo_url: str | None = None,
    title: str = "Оплата заказа",
    description: str = "Описание заказа",
    test: bool = False,
    user_bot_test: bool = False,
) -> dict:
    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_option = await option_db.get_option(custom_bot.options_id)

    prices = []
    if test:
        prices.append(
            LabeledPrice(
                label="Test Product",
                amount=100 * 100 if custom_bot.payment_type != BotPaymentTypeValues.STARS else 1,
            )
        )
        if not user_bot_test:
            provider_token = main_telegram_bot_settings.TEST_PROVIDER_TOKEN
        else:
            provider_token = custom_bot.provider_token
        payload = json.dumps({"bot_id": bot_id, "user_id": user_id, "order_id": "TEST"})
        photo_url = "https://static.vecteezy.com/system/resources/previews/000/442/267/original/vector-shop-icon.jpg"
    else:
        provider_token = custom_bot.provider_token
        for product_id, item in order_items.items():
            product = await product_db.get_product(product_id)
            if custom_bot.payment_type != BotPaymentTypeValues.STARS:
                price = product.price * 100
            else:
                price = product.price
            prices.append(
                LabeledPrice(
                    label=f"{product.name} x {item.amount}",
                    amount=price,
                )
            )
        payload = json.dumps({"bot_id": bot_id, "user_id": user_id, "order_id": order_id})

    if provider_token is None:
        provider_token = ""

    params = {
        "title": title,
        "description": description,
        "payload": payload,
        "provider_token": provider_token if custom_bot.payment_type != BotPaymentTypeValues.STARS else "",
        "currency": custom_bot_option.currency_code.value,
        "prices": prices,
        "photo_url": photo_url if custom_bot_option.show_photo_in_payment else None,
    }
    if custom_bot.payment_type != BotPaymentTypeValues.STARS:
        params["need_name"] = custom_bot_option.request_name_in_payment
        params["need_email"] = custom_bot_option.request_email_in_payment
        params["need_phone_number"] = custom_bot_option.request_phone_in_payment
        params["need_shipping_address"] = custom_bot_option.request_address_in_payment
    return params
