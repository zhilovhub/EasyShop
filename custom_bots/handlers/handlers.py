from aiogram.filters import CommandStart, CommandObject
import json
import random
import string
import time
from datetime import datetime, timedelta

from aiogram import F, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.keyboards import keyboards
from custom_bots.handlers.routers import multi_bot_router
from custom_bots.multibot import order_db, product_db, bot_db, main_bot, PREV_ORDER_MSGS, custom_bot_user_db, \
    CustomUserStates, QUESTION_MESSAGES, format_locales, channel_db, custom_ad_db
from database.models.bot_model import BotNotFound
from database.models.custom_bot_user_model import CustomBotUserNotFound
from database.models.order_model import OrderSchema, OrderStatusValues, OrderNotFound, OrderItem
from database.models.custom_ad_model import CustomAdSchemaWithoutId

from logs.config import custom_bot_logger, extra_params

from bot.utils.message_texts import MessageTexts


@multi_bot_router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    order_user_data = await event.bot.get_chat(user_id)

    try:
        data = json.loads(event.web_app_data.data)

        bot_id = data["bot_id"]

        custom_bot_logger.info(
            f"user_id={user_id}: received web app data: {data}",
            extra=extra_params(user_id=user_id, bot_id=bot_id)
        )

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
        random_string = ''.join(random.sample(
            string.digits + string.ascii_letters, 5))
        data['order_id'] = date + random_string

        order = OrderSchema(**data)
        order.ordered_at = order.ordered_at.replace(tzinfo=None)

        await order_db.add_order(order)

        custom_bot_logger.info(
            f"user_id={user_id}: order with order_id {order.id} is created",
            extra=extra_params(
                user_id=user_id, bot_id=bot_id, order_id=order.id)
        )
    except Exception as e:
        await event.answer("Произошла ошибка при создании заказа, администраторы уведомлены.")

        try:
            data = json.loads(event.web_app_data.data)
            bot_id = data["bot_id"]
        except Exception:
            bot_id = -1

        custom_bot_logger.error(
            f"user_id={user_id}: Unable to create an order in bot_id={bot_id}",
            extra=extra_params(user_id=user_id, bot_id=bot_id)
        )
        raise e

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


@multi_bot_router.message(CommandStart(deep_link=True))
async def start_cmd(message: Message, state: FSMContext, command: CommandObject):
    args = command.args
    user_id = message.from_user.id

    start_msg = await get_option("start_msg", message.bot.token)
    web_app_button = await get_option("web_app_button", message.bot.token)

    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
        custom_bot_logger.info(
            f"user_id={user_id}: user called /start at bot_id={bot.bot_id}",
            extra=extra_params(user_id=user_id, bot_id=bot.bot_id)
        )

        try:
            await custom_bot_user_db.get_custom_bot_user(bot.bot_id, user_id)
        except CustomBotUserNotFound:
            custom_bot_logger.info(
                f"user_id={user_id}: user not found in database, trying to add to it",
                extra=extra_params(user_id=user_id, bot_id=bot.bot_id)
            )
            await custom_bot_user_db.add_custom_bot_user(bot.bot_id, user_id)
    except BotNotFound:
        return await message.answer("Бот не инициализирован")

    await state.set_state(CustomUserStates.MAIN_MENU)
    await state.set_data({"bot_id": bot.bot_id})
    # await message.answer("Custom update works!")
    if args == "show_shop_inline":
        return await message.answer("Наш магазин:", reply_markup=keyboards.get_show_inline_button(bot.bot_id))

    return await message.answer(
        format_locales(start_msg, message.from_user, message.chat),
        reply_markup=keyboards.get_custom_bot_menu_keyboard(
            web_app_button, bot.bot_id)
    )


@multi_bot_router.message(lambda m: m.text == keyboards.CUSTOM_BOT_KEYBOARD_BUTTONS['partnership'])
async def partnership_handler(message: Message, state: FSMContext):
    bot_id = (await bot_db.get_bot_by_token(message.bot.token)).bot_id
    await message.answer(MessageTexts.CUSTOM_BOT_PARTNERSHIP.value,
                         reply_markup=keyboards.get_partnership_inline_kb(bot_id))


@multi_bot_router.callback_query(lambda q: q.data.startswith("request_ad"))
async def request_ad_handler(query: CallbackQuery, state: FSMContext):
    bot_id = int(query.data.split(':')[-1])
    bot_data = await bot_db.get_bot(bot_id)
    admin_user = await query.bot.get_chat(bot_data.created_by)
    await query.message.edit_text("Правила размещения рекламы:\n1. ...\n2. ...\n3. ...",
                                  reply_markup=keyboards.get_request_ad_keyboard(bot_id, admin_user.username))


@multi_bot_router.callback_query(lambda q: q.data.startswith("accept_ad"))
async def accept_ad_handler(query: CallbackQuery, state: FSMContext):
    bot_id = int(query.data.split(':')[-1])
    msg = await query.message.answer_photo(photo=FSInputFile("ad_example.jpg"),
                                           caption=MessageTexts.EXAMPLE_AD_POST_TEXT.value)
    await msg.reply("Условия для принятия:\n1. В канале должно быть 3 и более подписчиков."
                    "\n2. В течении 5 минут после рекламного поста нельзя публиковать посты."
                    "\n3. Время сделки: 10м."
                    "\n4. Стоимость: 1000руб.",
                    reply_markup=await keyboards.get_accept_ad_keyboard(bot_id))


@multi_bot_router.callback_query(lambda q: q.data.startswith("continue_ad_accept"))
async def continue_ad_accept_handler(query: CallbackQuery, state: FSMContext):
    bot_id = int(query.data.split(':')[-1])
    await query.message.edit_text("Выберите канал для отправки рекламного сообщения.",
                                  reply_markup=await keyboards.get_custom_bot_ad_channels_list_keyboard(bot_id))


@multi_bot_router.callback_query(lambda q: q.data.startswith("back_to_partnership"))
async def back_to_partnership(query: CallbackQuery, state: FSMContext):
    bot_id = int(query.data.split(':')[-1])
    await query.message.edit_text(MessageTexts.CUSTOM_BOT_PARTNERSHIP.value,
                                  reply_markup=keyboards.get_partnership_inline_kb(bot_id))


@multi_bot_router.callback_query(lambda q: q.data.startswith("ad_channel"))
async def ad_channel_handler(query: CallbackQuery, state: FSMContext):
    bot_id = int(query.data.split(':')[-2])
    chan_id = int(query.data.split(':')[-1])
    chan = await channel_db.get_channel(chan_id)
    channel_chat = await query.bot.get_chat(chan_id)
    members_count = await channel_chat.get_member_count()
    if members_count < 3:
        return await query.answer(f"В этом канале не достаточно подписчиков. ({members_count} < 3)",
                                  show_alert=True)
    msg = await query.bot.send_photo(chat_id=chan_id,
                                     photo=FSInputFile("ad_example.jpg"),
                                     caption=MessageTexts.EXAMPLE_AD_POST_TEXT.value)
    await query.message.edit_text("Сообщение отправлено в канал. Для завершения сделки, "
                                  "продолжайте соблюдать условия."
                                  "\n1. В канале должно быть 3 и более подписчиков."
                                  "\n2. В течении 5 минут после рекламного поста нельзя публиковать посты."
                                  "\n3. Время сделки: 10мин."
                                  "\n4. Стоимость: 1000руб.", reply_markup=None)
    chan.is_ad_post_block = True
    chan.ad_post_block_until = datetime.now() + timedelta(minutes=5)
    chan.ad_message_id = msg.message_id
    await channel_db.update_channel(chan)
    await custom_ad_db.add_ad(CustomAdSchemaWithoutId(channel_id=chan.channel_id,
                                                      message_id=msg.message_id,
                                                      time_until=datetime.now() + timedelta(minutes=10)))


@multi_bot_router.message(CustomUserStates.MAIN_MENU)
async def default_cmd(message: Message):
    web_app_button = await get_option("web_app_button", message.bot.token)

    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
        user_id = message.from_user.id

        custom_bot_logger.info(
            f"user_id={user_id}: user wrote {message.text} to bot_id={bot.bot_id}",
            extra=extra_params(user_id=user_id, bot_id=bot.bot_id)
        )
    except BotNotFound:
        custom_bot_logger.warning(
            f"bot_token={message.bot.token}: this bot is not in db",
            extra=extra_params(bot_token=message.bot.token)
        )
        return await message.answer("Бот не инициализирован")

    default_msg = await get_option("default_msg", message.bot.token)

    await message.answer(
        format_locales(default_msg, message.from_user, message.chat),
        reply_markup=keyboards.get_custom_bot_menu_keyboard(
            web_app_button, bot.bot_id)
    )


@multi_bot_router.callback_query(lambda q: q.data.startswith("order_"))
async def handle_order_callback(query: CallbackQuery):
    data = query.data.split(":")
    user_id = query.from_user.id

    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        custom_bot_logger.warning(
            f"user_id={user_id}: unable to change the status of order_id={data[1]}",
            extra=extra_params(user_id=user_id, order_id=data[1])
        )
        await query.answer("Ошибка при работе с заказом, возможно статус уже изменился", show_alert=True)
        return await query.message.edit_reply_markup(None)
    match data[0]:
        case "order_pre_cancel":
            custom_bot_logger.info(
                f"user_id={user_id}: tapped to pre_cancel in order_id={data[1]}",
                extra=extra_params(user_id=user_id, order_id=data[1])
            )
            await query.message.edit_reply_markup(reply_markup=keyboards.create_cancel_confirm_kb(data[1]))
        case "order_back_to_order":
            custom_bot_logger.info(
                f"user_id={user_id}: backed to menu of order_id={data[1]}",
                extra=extra_params(user_id=user_id, order_id=data[1])
            )
            await query.message.edit_reply_markup(reply_markup=keyboards.create_user_order_kb(data[1]))
        case "order_cancel":
            custom_bot_logger.info(
                f"user_id={user_id}: tapped to cancel the order_id={data[1]}",
                extra=extra_params(user_id=user_id, order_id=data[1])
            )

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

            custom_bot_logger.info(
                f"order_id={data[1]}: is cancelled by custom_user with user_id={user_id}",
                extra=extra_params(user_id=user_id, order_id=data[1])
            )


@multi_bot_router.callback_query(lambda q: q.data.startswith("ask_question"))
async def handle_ask_question_callback(query: CallbackQuery, state: FSMContext):
    data = query.data.split(":")
    user_id = query.from_user.id

    custom_bot_logger.info(
        f"user_id={user_id}: wants to ask the question regarding order by order_id={data[1]}",
        extra=extra_params(user_id=user_id, order_id=data[1])
    )

    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        custom_bot_logger.warning(
            f"user_id={user_id}: tried to ask the question regarding order by order_id={data[1]} is not found",
            extra=extra_params(user_id=user_id, order_id=data[1])
        )
        await query.answer("Ошибка при работе с заказом, возможно заказ был удалён", show_alert=True)
        return await query.message.edit_reply_markup(None)

    state_data = await state.get_data()

    if not state_data:
        state_data = {"order_id": order.id}
    else:
        if "last_question_time" in state_data and time.time() - state_data['last_question_time'] < 1 * 60 * 60:
            custom_bot_logger.info(
                f"user_id={user_id}: too early for asking question about order_id={order.id}",
                extra=extra_params(user_id=user_id, order_id=order.id)
            )
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
    user_id = message.from_user.id

    if not state_data or 'order_id' not in state_data:
        custom_bot_logger.error(
            f"user_id={user_id}: unable to accept a question due to lost order_id from state_data",
            extra=extra_params(user_id=user_id)
        )

        await state.set_state(CustomUserStates.MAIN_MENU)
        return await message.answer("Произошла ошибка возвращаюсь в главное меню...")

    order_id = state_data['order_id']
    custom_bot_logger.info(
        f"user_id={user_id}: sent question regarded to order_id={order_id}",
        extra=extra_params(user_id=user_id, order_id=order_id)
    )

    await message.reply(f"Вы уверены что хотите отправить это сообщение вопросом к заказу "
                        f"<b>#{order_id}</b>?"
                        f"\n\nПосле отправки вопроса, Вы сможете отправить следующий <b>минимум через 1 час</b> или "
                        f"<b>после ответа администратора</b>",
                        reply_markup=keyboards.create_confirm_question_kb(
                            order_id=order_id,
                            msg_id=message.message_id,
                            chat_id=message.chat.id
                        ))


@multi_bot_router.callback_query(lambda q: q.data.startswith("approve_ask_question"))
async def approve_ask_question_callback(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    user_id = query.from_user.id
    data = query.data.split(":")

    custom_bot_logger.info(
        f"user_id={user_id}: approving question regarded to order_id={data[1]} from db",
        extra=extra_params(user_id=user_id, order_id=data[1])
    )

    if not state_data or 'order_id' not in state_data:
        custom_bot_logger.error(
            f"user_id={user_id}: unable to approve question due to lost order_id={data[1]} from state_data",
            extra=extra_params(user_id=user_id, order_id=data[1])
        )

        await state.set_state(CustomUserStates.MAIN_MENU)
        await query.message.edit_reply_markup(None)
        return await query.answer("Произошла ошибка возвращаюсь в главное меню...", show_alert=True)

    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        custom_bot_logger.warning(
            f"user_id={user_id}: unable to approve question due to lost order_id={data[1]} from db",
            extra=extra_params(user_id=user_id, order_id=data[1])
        )
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

        custom_bot_logger.info(
            f"user_id={bot_data.created_by}: got question regarded to order_id={order.id} from user_id={user_id}",
            extra=extra_params(user_id=bot_data.created_by, order_id=order.id)
        )

    except TelegramAPIError:
        await main_bot.send_message(chat_id=bot_data.created_by,
                                    text="Вам поступило новое <b>сообщение-вопрос</b> от клиента, "
                                         "но Вашему боту <b>не удалось Вам его отправить</b>, "
                                         "проверьте писали ли Вы хоть раз своему боту и не заблокировали ли вы его"
                                         f"\n\n* ссылка на Вашего бота @{(await query.bot.get_me()).username}")

        custom_bot_logger.error(
            f"user_id={bot_data.created_by}: couldn't get question regarded to order_id={order.id} from user_id={user_id}",
            extra=extra_params(user_id=bot_data.created_by, order_id=order.id)
        )
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
    custom_bot_logger.info(
        f"user_id={query.from_user.id}: cancelled asking question about order",
        extra=extra_params(user_id=query.from_user.id)
    )

    await query.answer("Отправка вопроса администратору отменена\nВозвращаемся в меню", show_alert=True)
    await state.set_state(CustomUserStates.MAIN_MENU)
    await query.message.edit_reply_markup(reply_markup=None)


async def get_option(param: str, token: str):
    try:
        bot_info = await bot_db.get_bot_by_token(token)
    except BotNotFound:
        custom_bot_logger.warning(
            f"bot_token={token}: this bot is not in db. Deleting webhook...",
            extra=extra_params(bot_token=token)
        )
        return await Bot(token).delete_webhook()

    options = bot_info.settings
    if options is None:
        custom_bot_logger.warning(
            f"bot_id={bot_info.bot_id}: bot has empty settings",
            extra=extra_params(bot_id=bot_info.bot_id)
        )
        return None

    if param in options:
        return options[param]

    custom_bot_logger.warning(
        f"bot_id={bot_info.bot_id}: {param} not in settings",
        extra=extra_params(bot_id=bot_info.bot_id)
    )
    return None
