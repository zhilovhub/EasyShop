import json

from aiogram import F, Bot
from aiogram.enums import ParseMode
from aiogram.types import Message

from custom_bots.multibot import bot_db, main_bot, PREV_ORDER_MSGS, \
    CustomUserStates, format_locales
from custom_bots.handlers.routers import multi_bot_router
from common_utils.order_utils.order_type import OrderType
from custom_bots.utils.custom_bot_options import get_option
from common_utils.order_utils.order_utils import create_order
from custom_bots.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard

from database.config import product_db, order_db
from database.models.bot_model import BotNotFound
from database.models.product_model import NotEnoughProductsInStockToReduce

from common_utils.keyboards.order_manage_keyboards import InlineOrderStatusesKeyboard, InlineOrderCustomBotKeyboard

from logs.config import custom_bot_logger, extra_params


@multi_bot_router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    order_user_data = await event.bot.get_chat(user_id)

    try:
        order = await create_order(event, OrderType.CUSTOM_BOT_ORDER)
        bot_id = order.bot_id

        await order_db.add_order(order)

        products = [(await product_db.get_product(product_id), product_item.amount, product_item.used_extra_options)
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
