import json
import random
import string
from datetime import datetime

from aiogram import F, Bot
from aiogram.enums import ParseMode
from aiogram.types import Message

from custom_bots.multibot import bot_db, main_bot, PREV_ORDER_MSGS, \
    CustomUserStates, format_locales
from custom_bots.handlers.routers import multi_bot_router
from custom_bots.utils.custom_bot_options import get_option
from custom_bots.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard

from database.config import product_db, order_db
from database.models.bot_model import BotNotFound
from database.models.order_model import OrderSchema, OrderItem
from database.models.product_model import NotEnoughProductsInStockToReduce

from common_utils.keyboards.order_manage_keyboards import InlineOrderStatusesKeyboard, InlineOrderCustomBotKeyboard

from logs.config import custom_bot_logger, extra_params


@multi_bot_router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    order_user_data = await event.bot.get_chat(user_id)

    try:
        data = json.loads(event.web_app_data.data)

        bot_id = data["bot_id"]
        bot_data = await bot_db.get_bot(int(bot_id))

        custom_bot_logger.info(
            f"user_id={user_id}: received web app data: {data}",
            extra=extra_params(user_id=user_id, bot_id=bot_id)
        )

        data["from_user"] = user_id
        data["payment_method"] = "Картой Онлайн"
        data["status"] = "backlog"

        items: dict[int, OrderItem] = {}

        zero_products = []

        for item_id, item in data['raw_items'].items():
            product = await product_db.get_product(item_id)
            chosen_options = {}
            used_options = False
            if 'chosen_option' in item and item['chosen_option']:
                used_options = True
                option_title = list(product.extra_options.items())[0][0]
                chosen_options[option_title] = item['chosen_option']
            items[item_id] = OrderItem(amount=item['amount'], used_extra_option=used_options,
                                       extra_options=chosen_options)
            if bot_data.settings and "auto_reduce" in bot_data.settings and bot_data.settings["auto_reduce"]:
                if product.count < item['amount']:
                    raise NotEnoughProductsInStockToReduce(product, item['amount'])
                product.count -= item['amount']
                if product.count == 0:
                    zero_products.append(product)
                await product_db.update_product(product)

        if zero_products:
            msg = await main_bot.send_message(bot_data.created_by,
                                              "⚠️ Внимание, после этого заказа кол-во следующих товаров будет равно 0.")
            await msg.reply("\n".join([f"{p.name} [{p.id}]" for p in zero_products]))

        data['items'] = items

        date = datetime.now().strftime("%d%m%y")
        random_string = ''.join(random.sample(
            string.digits + string.ascii_letters, 5))
        data['order_id'] = date + random_string

        order = OrderSchema(**data)
        order.ordered_at = order.ordered_at.replace(tzinfo=None)

        await order_db.add_order(order)

        products = [(await product_db.get_product(product_id), product_item.amount, product_item.extra_options)
                    for product_id, product_item in order.items.items()]
        username = "@" + order_user_data.username if order_user_data.username else order_user_data.full_name
        admin_id = (await bot_db.get_bot_by_token(event.bot.token)).created_by
        main_msg = await main_bot.send_message(
            admin_id, order.convert_to_notification_text(
                products,
                username,
                True
            ))

        msg_id_data = PREV_ORDER_MSGS.get_data()
        msg_id_data[order.id] = (main_msg.chat.id, main_msg.message_id)
        PREV_ORDER_MSGS.update_data(msg_id_data)
        msg = await event.bot.send_message(
            user_id, order.convert_to_notification_text(
                products,
                username,
                False
            ), reply_markup=InlineOrderCustomBotKeyboard.get_keyboard(order.id)
        )
        post_order_text = await get_option("post_order_msg", event.bot.token)
        if post_order_text:
            await event.bot.send_message(
                chat_id=user_id,
                text=post_order_text,
                parse_mode=ParseMode.HTML
            )

        await main_bot.edit_message_reply_markup(
            main_msg.chat.id,
            main_msg.message_id,
            reply_markup=InlineOrderStatusesKeyboard.get_keyboard(
                order.id, msg.message_id, msg.chat.id, current_status=order.status
            )
        )

        custom_bot_logger.info(
            f"user_id={user_id}: order with order_id {order.id} is created",
            extra=extra_params(
                user_id=user_id, bot_id=bot_id, order_id=order.id)
        )
    except NotEnoughProductsInStockToReduce as e:
        await event.answer(
            f":(\nК сожалению на складе недостаточно <b>{e.product.name}</b> для выполнения Вашего заказа."
        )
    except Exception as e:
        await event.answer("Произошла ошибка при создании заказа, администраторы уведомлены.")

        try:
            data = json.loads(event.web_app_data.data)
            bot_id = data["bot_id"]
        except Exception as another_e:
            bot_id = -1
            custom_bot_logger.error(
                f"user_id={user_id}: Unable to find bot_id from event.web_app_data.data",
                extra=extra_params(user_id=user_id),
                exc_info=another_e
            )

        custom_bot_logger.error(
            f"user_id={user_id}: Unable to create an order in bot_id={bot_id}",
            extra=extra_params(user_id=user_id, bot_id=bot_id),
            exc_info=e
        )
        raise e


@multi_bot_router.message(CustomUserStates.MAIN_MENU)
async def main_menu_handler(message: Message):
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
    except BotNotFound:
        custom_bot_logger.warning(
            f"bot_token={message.bot.token}: this bot is not in db",
            extra=extra_params(bot_token=message.bot.token)
        )
        await Bot(message.bot.token).delete_webhook()
        return await message.answer("Бот не инициализирован")

    match message.text:
        case _:
            default_msg = await get_option("default_msg", message.bot.token)

            await message.answer(
                format_locales(default_msg, message.from_user, message.chat),
                reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(
                    bot.bot_id
                )
            )
