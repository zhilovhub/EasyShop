import json
import random
import string
from datetime import datetime

from aiogram import Bot
from aiogram.types import Message

from common_utils.bot_settings_config import BOT_PROPERTIES
from common_utils.env_config import TELEGRAM_TOKEN
from common_utils.order_utils.order_type import OrderType, UnknownOrderType

from database.config import bot_db, product_db
from database.models.order_model import OrderSchema, OrderItem, OrderItemExtraOption
from database.models.product_model import NotEnoughProductsInStockToReduce

from logs.config import logger, custom_bot_logger, extra_params


async def create_order(event: Message, order_type: OrderType) -> OrderSchema:
    data = json.loads(event.web_app_data.data)

    user_id = event.from_user.id
    bot_id = data["bot_id"]
    bot_data = await bot_db.get_bot(int(bot_id))

    match order_type:
        case OrderType.MAIN_BOT_TEST_ORDER:
            current_logger = logger
        case OrderType.CUSTOM_BOT_ORDER:
            current_logger = custom_bot_logger
        case _:
            raise UnknownOrderType(order_type)

    current_logger.info(
        f"user_id={user_id}: received web app data: {data}",
        extra=extra_params(user_id=user_id, bot_id=bot_id)
    )

    data["from_user"] = user_id
    data["payment_method"] = "Картой Онлайн"
    data["status"] = "backlog"

    items: dict[int, OrderItem] = {}

    zero_products = []

    for product_id, item in data['raw_items'].items():
        product = await product_db.get_product(int(product_id))
        chosen_options = []

        if 'chosen_options' in item and item['chosen_options']:
            for option in item['chosen_options']:
                need_option = None
                for opt in product.extra_options:
                    if opt.name == option["name"]:
                        need_option = opt
                        break
                price = 0
                if need_option.variants_prices:
                    for i, var in enumerate(need_option.variants):
                        if var == option['selected_variant']:
                            price = need_option.variants_prices[i]
                            break
                chosen_options.append(OrderItemExtraOption(name=option['name'],
                                                           selected_variant=option['selected_variant'],
                                                           price=price))

        items[product_id] = OrderItem(
            amount=item['amount'],
            used_extra_options=chosen_options
        )

        if bot_data.settings and "auto_reduce" in bot_data.settings and bot_data.settings["auto_reduce"]:
            # check if owner wants to get order or not
            # if product.count < item['amount']:
            #     raise NotEnoughProductsInStockToReduce(product, item['amount'])

            product.count -= item['amount']
            # if product.count == 0:
            #     zero_products.append(product)
            if product.count < 0:
                product.count = 0

            await product_db.update_product(product)

    # await _handle_zero_products(event, bot_data.created_by, zero_products, order_type)

    data['items'] = items

    date = datetime.now().strftime("%d%m%y")
    random_string = ''.join(random.sample(string.digits + string.ascii_letters, 5))
    data['order_id'] = date + random_string

    return _form_order(data, order_type)


# Old text generation
async def _handle_zero_products(event: Message, bot_owner: int, zero_products: list, order_type: OrderType) -> None:
    if zero_products:
        text = "⚠️ Внимание, после этого заказа кол-во следующих товаров будет равно 0"

        match order_type:
            case OrderType.MAIN_BOT_TEST_ORDER:
                msg = await event.answer(text)
            case OrderType.CUSTOM_BOT_ORDER:
                msg = await Bot(TELEGRAM_TOKEN, default=BOT_PROPERTIES).send_message(bot_owner, text)
            case _:
                raise UnknownOrderType(order_type)

        await msg.reply("\n".join([f"{p.name} [{p.id}]" for p in zero_products]))


def _form_order(data: dict, order_type: OrderType) -> OrderSchema:
    order = OrderSchema(**data)
    match order_type:
        case OrderType.MAIN_BOT_TEST_ORDER:
            pass
        case OrderType.CUSTOM_BOT_ORDER:
            order.ordered_at = order.ordered_at.replace(tzinfo=None)
        case _:
            raise UnknownOrderType(order_type)

    return order
