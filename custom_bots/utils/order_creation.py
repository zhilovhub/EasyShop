from common_utils.bot_utils import create_bot_options
from database.models.option_model import OptionNotFoundError
from database.models.order_model import OrderSchema
from database.config import order_db, product_db, bot_db, option_db

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import Chat

from custom_bots.multibot import main_bot, PREV_ORDER_MSGS

from custom_bots.utils.custom_message_texts import CustomMessageTexts

from common_utils.message_texts import MessageTexts as CommonMessageTexts
from common_utils.keyboards.order_manage_keyboards import InlineOrderStatusesKeyboard, InlineOrderCustomBotKeyboard

from logs.config import extra_params, custom_bot_logger


async def order_creation_process(order: OrderSchema, order_user_data: Chat):
    bot_id = order.bot_id
    user_id = order_user_data.id

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_tg = Bot(custom_bot.token)

    await order_db.add_order(order)

    products = []
    for product_id, order_item in order.items.items():
        product = await product_db.get_product(product_id)
        products.append((product, order_item.amount, order_item.used_extra_options))
    username = "@" + order_user_data.username if order_user_data.username else order_user_data.full_name

    # TODO Handle exceptions
    custom_bot = await bot_db.get_bot_by_token(custom_bot.token)

    admin_id = custom_bot.created_by

    text = await CommonMessageTexts.generate_order_notification_text(
        order,
        products,
        username,
        True
    )
    main_msg = await main_bot.send_message(
        admin_id, **text
    )
    products_to_refill = []
    products_not_enough = []
    try:
        options = await option_db.get_option(custom_bot.options_id)
    except OptionNotFoundError:
        new_options_id = await create_bot_options()
        custom_bot.options_id = new_options_id
        await bot_db.update_bot(custom_bot)
        options = await option_db.get_option(new_options_id)
    if options.auto_reduce is True:
        for ind, product_item in enumerate(products, start=1):
            product_schema, amount, extra_options = product_item
            if product_schema.count <= amount:
                products_to_refill.append(product_schema)
                if product_schema.count < amount:
                    products_not_enough.append(product_schema)

    msg_id_data = PREV_ORDER_MSGS.get_data()
    msg_id_data[order.id] = (main_msg.chat.id, main_msg.message_id)
    PREV_ORDER_MSGS.update_data(msg_id_data)
    text = await CommonMessageTexts.generate_order_notification_text(
        order,
        products,
        username,
        False
    )
    msg = await custom_bot_tg.send_message(
        chat_id=user_id, reply_markup=InlineOrderCustomBotKeyboard.get_keyboard(order.id), **text
    )

    if len(products_to_refill) != 0:
        await main_bot.send_message(
            chat_id=admin_id,
            reply_to_message_id=main_msg.message_id,
            **CustomMessageTexts.generate_stock_info_to_refill(products_to_refill, order.id)
        )
    if len(products_not_enough) != 0:
        await main_bot.send_message(
            chat_id=admin_id,
            reply_to_message_id=main_msg.message_id,
            **CustomMessageTexts.generate_not_enough_in_stock(products_not_enough, order.id)
        )

    post_order_text = options.post_order_msg
    if post_order_text:
        await custom_bot_tg.send_message(
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
