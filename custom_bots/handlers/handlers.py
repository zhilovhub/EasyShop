import json
import random
import string
import time
from datetime import datetime

from aiogram import F, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import keyboards
from custom_bots.handlers.routers import multi_bot_router
from custom_bots.multibot import order_db, product_db, bot_db, main_bot, PREV_ORDER_MSGS, custom_bot_user_db, CustomUserStates, QUESTION_MESSAGES, format_locales
from database.models.bot_model import BotNotFound
from database.models.custom_bot_user_model import CustomBotUserNotFound
from database.models.order_model import OrderSchema, OrderStatusValues, OrderNotFound, OrderItem

from logs.config import logger


@multi_bot_router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    order_user_data = await event.bot.get_chat(user_id)

    try:
        data = json.loads(event.web_app_data.data)
        logger.info(f"receive web app data: {data}")

        data["from_user"] = user_id
        data["payment_method"] = "Картой Онлайн"
        data["status"] = "backlog"

        items: dict[int, OrderItem] = {}

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

        data['items'] = items

        date = datetime.now().strftime("%d%m%y")
        random_string = ''.join(random.sample(string.digits + string.ascii_letters, 5))
        data['order_id'] = date + random_string

        order = OrderSchema(**data)
        order.ordered_at = order.ordered_at.replace(tzinfo=None)

        await order_db.add_order(order)

        logger.info(f"order with id #{order.id} created")
    except Exception:
        logger.error("error while creating order", exc_info=True)
        return await event.answer("Произошла ошибка при создании заказа, попробуйте еще раз.")

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
        ), reply_markup=keyboards.create_user_order_kb(order.id)
    )
    await main_bot.edit_message_reply_markup(
        main_msg.chat.id,
        main_msg.message_id,
        reply_markup=keyboards.create_change_order_status_kb(order.id, msg.message_id, msg.chat.id,
                                                             current_status=order.status)
    )


@multi_bot_router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    start_msg = await get_option("start_msg", message.bot.token)
    web_app_button = await get_option("web_app_button", message.bot.token)
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
        try:
            await custom_bot_user_db.get_custom_bot_user(bot.bot_id, message.from_user.id)
        except CustomBotUserNotFound:
            logger.info(
                f"custom_user {message.from_user.id} of bot_id {bot.bot_id} not found in db, creating new instance..."
            )
            await custom_bot_user_db.add_custom_bot_user(bot.bot_id, message.from_user.id)
    except BotNotFound:
        return await message.answer("Бот не инициализирован")

    await state.set_state(CustomUserStates.MAIN_MENU)

    return await message.answer(
        format_locales(start_msg, message.from_user, message.chat),
        reply_markup=keyboards.get_custom_bot_menu_keyboard(web_app_button, bot.bot_id)
    )


@multi_bot_router.message(CustomUserStates.MAIN_MENU)
async def default_cmd(message: Message):
    web_app_button = await get_option("web_app_button", message.bot.token)

    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
    except BotNotFound:
        return await message.answer("Бот не инициализирован")

    default_msg = await get_option("default_msg", message.bot.token)
    await message.answer(
        format_locales(default_msg, message.from_user, message.chat),
        reply_markup=keyboards.get_custom_bot_menu_keyboard(web_app_button, bot.bot_id)
    )


@multi_bot_router.callback_query(lambda q: q.data.startswith("order_"))
async def handle_order_callback(query: CallbackQuery):
    data = query.data.split(":")
    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        await query.answer("Ошибка при работе с заказом, возможно статус уже изменился", show_alert=True)
        return await query.message.edit_reply_markup(None)
    match data[0]:
        case "order_pre_cancel":
            await query.message.edit_reply_markup(reply_markup=keyboards.create_cancel_confirm_kb(data[1]))
        case "order_back_to_order":
            await query.message.edit_reply_markup(reply_markup=keyboards.create_user_order_kb(data[1]))
        case "order_cancel":
            order.status = OrderStatusValues.CANCELLED
            await order_db.update_order(order)
            products = [(await product_db.get_product(int(product_id)), product_item.amount, product_item.extra_options)
                        for product_id, product_item in order.items.items()]
            await query.message.edit_text(order.convert_to_notification_text(products=products), reply_markup=None)
            msg_id_data = PREV_ORDER_MSGS.get_data()
            await main_bot.edit_message_text(
                text=order.convert_to_notification_text(
                    products=products,
                    username="@" + query.from_user.username if query.from_user.username else query.from_user.full_name,
                    is_admin=True
                ), chat_id=msg_id_data[order.id][0], message_id=msg_id_data[order.id][1], reply_markup=None)
            await main_bot.send_message(
                chat_id=msg_id_data[order.id][0],
                text=f"Новый статус заказа <b>#{order.id}</b>\n<b>{order.translate_order_status()}</b>")
            del msg_id_data[order.id]


@multi_bot_router.callback_query(lambda q: q.data.startswith("ask_question"))
async def handle_ask_question_callback(query: CallbackQuery, state: FSMContext):
    data = query.data.split(":")

    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        await query.answer("Ошибка при работе с заказом, возможно заказ был удалён", show_alert=True)
        return await query.message.edit_reply_markup(None)

    state_data = await state.get_data()
    if not state_data:
        state_data = {"order_id": order.id}
    else:
        if "last_question_time" in state_data and time.time() - state_data['last_question_time'] < 1 * 60 * 60:
            return await query.answer("Вы уже задавали вопрос недавно, пожалуйста, попробуйте позже "
                                      "(между вопросами должен пройти час)", show_alert=True)
        state_data['order_id'] = order.id

    await state.set_state(CustomUserStates.WAITING_FOR_QUESTION)
    await query.message.answer(
        "Вы можете отправить свой вопрос по заказу, отправив любое сообщение боту",
        reply_markup=keyboards.get_back_keyboard()
    )
    await state.set_data(state_data)


@multi_bot_router.message(CustomUserStates.WAITING_FOR_QUESTION)
async def handle_waiting_for_question_state(message: Message, state: FSMContext):
    state_data = await state.get_data()

    if not state_data or 'order_id' not in state_data:
        await state.set_state(CustomUserStates.MAIN_MENU)
        return await message.answer("Произошла ошибка возвращаюсь в главное меню...")

    await message.reply(f"Вы уверены что хотите отправить это сообщение вопросом к заказу "
                        f"<b>#{state_data['order_id']}</b>?"
                        f"\n\nПосле отправки вопроса, Вы сможете отправить следующий <b>минимум через 1 час</b> или "
                        f"<b>после ответа администратора</b>",
                        reply_markup=keyboards.create_confirm_question_kb(
                            order_id=state_data['order_id'],
                            msg_id=message.message_id,
                            chat_id=message.chat.id
                        ))


@multi_bot_router.callback_query(lambda q: q.data.startswith("approve_ask_question"))
async def approve_ask_question_callback(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()

    if not state_data or 'order_id' not in state_data:
        await state.set_state(CustomUserStates.MAIN_MENU)
        await query.message.edit_reply_markup(None)
        return await query.answer("Произошла ошибка возвращаюсь в главное меню...", show_alert=True)

    data = query.data.split(":")
    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        await query.answer("Ошибка при работе с заказом, возможно заказ был удалён", show_alert=True)
        return await query.message.edit_reply_markup(None)

    bot_data = await bot_db.get_bot_by_token(query.bot.token)
    try:
        message = await main_bot.send_message(chat_id=bot_data.created_by,
                                              text=f"Новый вопрос по заказу <b>#{order.id}</b> от пользователя "
                                                   f"<b>{'@' + query.from_user.username if query.from_user.username else query.from_user.full_name}</b> 👇\n\n"
                                                   f"<i>{query.message.reply_to_message.text}</i>\n\n"
                                                   f"Для ответа на вопрос <b>зажмите это сообщение</b> и ответьте на него")
        question_messages_data = QUESTION_MESSAGES.get_data()
        question_messages_data[message.message_id] = {
            "question_from_custom_bot_message_id": data[2],
            "order_id": order.id
        }
        QUESTION_MESSAGES.update_data(question_messages_data)
    except TelegramAPIError:
        await main_bot.send_message(chat_id=bot_data.created_by,
                                    text="Вам поступило новое <b>сообщение-вопрос</b> от клиента, "
                                         "но Вашему боту <b>не удалось Вам его отправить</b>, "
                                         "проверьте писали ли Вы хоть раз своему боту и не заблокировали ли вы его"
                                         f"\n\n* ссылка на Вашего бота @{(await query.bot.get_me()).username}")

        logger.info("cant send order question to admin", exc_info=True)
        await state.set_state(CustomUserStates.MAIN_MENU)
        return await query.answer(":( Не удалось отправить Ваш вопрос", show_alert=True)

    await query.message.edit_text(
        "Ваш вопрос отправлен, ожидайте ответа от администратора магазина в этом чате", reply_markup=None
    )

    state_data['last_question_time'] = time.time()

    await state.set_state(CustomUserStates.MAIN_MENU)
    await state.set_data(state_data)


@multi_bot_router.callback_query(lambda q: q.data.startswith("cancel_ask_question"))
async def cancel_ask_question_callback(query: CallbackQuery, state: FSMContext):
    await query.answer("Отправка вопроса администратору отменена\nВозвращаемся в меню", show_alert=True)
    await state.set_state(CustomUserStates.MAIN_MENU)
    await query.message.edit_reply_markup(reply_markup=None)


async def get_option(param: str, token: str):
    try:
        bot_info = await bot_db.get_bot_by_token(token)
    except BotNotFound:
        return await Bot(token).delete_webhook()

    options = bot_info.settings
    if options is None:
        return None
    if param in options:
        return options[param]
    return None
