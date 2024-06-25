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
from bot.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard
from bot.keyboards.order_manage_keyboards import InlineOrderStatusesKeyboard, InlineOrderCancelKeyboard, \
    InlineOrderCustomBotKeyboard
from bot.keyboards.question_keyboards import InlineOrderQuestionKeyboard
from custom_bots.handlers.routers import multi_bot_router
from custom_bots.multibot import order_db, product_db, bot_db, main_bot, PREV_ORDER_MSGS, custom_bot_user_db, \
    CustomUserStates, QUESTION_MESSAGES, format_locales, channel_db, custom_ad_db, scheduler, user_db
from database.models.bot_model import BotNotFound
from database.models.custom_bot_user_model import CustomBotUserNotFound
from database.models.order_model import OrderSchema, OrderStatusValues, OrderNotFound, OrderItem
from database.models.custom_ad_model import CustomAdSchemaWithoutId, CustomAdSchema
from database.models.product_model import NotEnoughProductsInStockToReduce

from logs.config import custom_bot_logger, extra_params

from bot.utils.message_texts import MessageTexts


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
            if bot_data.settings and "auto_reduce" in bot_data.settings and bot_data.settings["auto_reduce"] == True:
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

        custom_bot_logger.info(
            f"user_id={user_id}: order with order_id {order.id} is created",
            extra=extra_params(
                user_id=user_id, bot_id=bot_id, order_id=order.id)
        )
    except Exception as e:
        if isinstance(e, NotEnoughProductsInStockToReduce):
            await event.answer(
                f":(\nК сожалению на складе недостаточно <b>{product.name}</b> для выполнения Вашего заказа.")
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
        ), reply_markup=InlineOrderCustomBotKeyboard.get_keyboard(order.id)
    )
    await main_bot.edit_message_reply_markup(
        main_msg.chat.id,
        main_msg.message_id,
        reply_markup=InlineOrderStatusesKeyboard.get_keyboard(
            order.id, msg.message_id, msg.chat.id, current_status=order.status
        )
    )


@multi_bot_router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext, command: CommandObject):
    user_id = message.from_user.id

    start_msg = await get_option("start_msg", message.bot.token)

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

    if command.args == "show_shop_inline":
        return await message.answer("Наш магазин:", reply_markup=keyboards.get_show_inline_button(bot.bot_id))

    await message.answer(
        format_locales(start_msg, message.from_user, message.chat),
        reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(
            bot.bot_id
        )
    )
    await state.set_state(CustomUserStates.MAIN_MENU)


@multi_bot_router.callback_query(lambda q: q.data.startswith("request_ad"))
async def request_ad_handler(query: CallbackQuery):
    bot_id = int(query.data.split(':')[-1])
    bot_data = await bot_db.get_bot(bot_id)
    admin_user = await query.bot.get_chat(bot_data.created_by)
    await query.message.edit_text("Правила размещения рекламы:\n1. ...\n2. ...\n3. ...",
                                  reply_markup=keyboards.get_request_ad_keyboard(bot_id, admin_user.username))


@multi_bot_router.callback_query(lambda q: q.data.startswith("accept_ad"))
async def accept_ad_handler(query: CallbackQuery):
    bot_id = int(query.data.split(':')[-1])
    msg = await query.message.answer_photo(photo=FSInputFile("ad_example.jpg"),
                                           caption=MessageTexts.EXAMPLE_AD_POST_TEXT.value)
    await msg.reply("Условия для принятия:\n1. В канале должно быть 3 и более подписчиков."
                    "\n2. В течении 5 минут после рекламного поста нельзя публиковать посты."
                    "\n3. Время сделки: 10м."
                    "\n4. Стоимость: 1000руб.",
                    reply_markup=await keyboards.get_accept_ad_keyboard(bot_id))


@multi_bot_router.callback_query(lambda q: q.data.startswith("continue_ad_accept"))
async def continue_ad_accept_handler(query: CallbackQuery):
    bot_id = int(query.data.split(':')[-1])
    await query.message.edit_text("Выберите канал для отправки рекламного сообщения.",
                                  reply_markup=await keyboards.get_custom_bot_ad_channels_list_keyboard(bot_id))


@multi_bot_router.callback_query(lambda q: q.data.startswith("back_to_partnership"))
async def back_to_partnership(query: CallbackQuery):
    bot_id = int(query.data.split(':')[-1])
    await query.message.edit_text(MessageTexts.CUSTOM_BOT_PARTNERSHIP.value,
                                  reply_markup=keyboards.get_partnership_inline_kb(bot_id))


async def complete_custom_ad_request(channel_id: int, bot_id: int):
    bot_data = await bot_db.get_bot(bot_id)
    bot = Bot(token=bot_data.token)

    adv = await custom_ad_db.get_channel_last_custom_ad(channel_id=channel_id)
    adv.status = "finished"

    channel = await channel_db.get_channel(channel_id)
    channel.is_ad_post_block = False
    await channel_db.update_channel(channel)

    await bot.send_message(adv.by_user, "Рекламное предложение завершено, на Ваш баланс зачислено 1000руб.")

    user = await custom_bot_user_db.get_custom_bot_user(bot_id, adv.by_user)
    user.balance += 1000

    admin_user = await user_db.get_user(bot_data.created_by)
    admin_user.balance -= 1000

    await user_db.update_user(admin_user)
    await custom_bot_user_db.update_custom_bot_user(user)


@multi_bot_router.callback_query(lambda q: q.data.startswith("ad_channel"))
async def ad_channel_handler(query: CallbackQuery):
    bot_id = int(query.data.split(':')[-2])
    channel_id = int(query.data.split(':')[-1])
    channel = await channel_db.get_channel(channel_id)
    channel_chat = await query.bot.get_chat(channel_id)
    members_count = await channel_chat.get_member_count()
    bot_data = await bot_db.get_bot(bot_id)
    admin_user = await user_db.get_user(bot_data.created_by)
    if admin_user.balance < 1000:
        return await query.answer("В данный момент администратор канала не готов принимать рекламные предложения"
                                  " (на балансе нет средств)")
    if members_count < 3:
        return await query.answer(f"В этом канале не достаточно подписчиков. ({members_count} < 3)",
                                  show_alert=True)
    msg = await query.bot.send_photo(chat_id=channel_id,
                                     photo=FSInputFile("ad_example.jpg"),
                                     caption=MessageTexts.EXAMPLE_AD_POST_TEXT.value)
    await query.message.edit_text("Сообщение отправлено в канал. Для завершения сделки, "
                                  "продолжайте соблюдать условия."
                                  "\n1. В канале должно быть 3 и более подписчиков."
                                  "\n2. В течении 5 минут после рекламного поста нельзя публиковать посты."
                                  "\n3. Время сделки: 10мин."
                                  "\n4. Стоимость: 1000руб.", reply_markup=None)
    channel.is_ad_post_block = True
    channel.ad_post_block_until = datetime.now() + timedelta(minutes=5)
    await channel_db.update_channel(channel)
    job_id = await scheduler.add_scheduled_job(complete_custom_ad_request,
                                               (datetime.now() + timedelta(minutes=10)).replace(tzinfo=None),
                                               [channel.channel_id, bot_id])
    await custom_ad_db.add_ad(CustomAdSchemaWithoutId(channel_id=channel.channel_id,
                                                      message_id=msg.message_id,
                                                      time_until=datetime.now() + timedelta(minutes=10),
                                                      status="active",
                                                      finish_job_id=job_id,
                                                      by_user=query.from_user.id))


@multi_bot_router.message(CustomUserStates.MAIN_MENU)
async def main_menu_handler(message: Message):
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
        user_id = message.from_user.id
    except BotNotFound:
        custom_bot_logger.warning(
            f"bot_token={message.bot.token}: this bot is not in db",
            extra=extra_params(bot_token=message.bot.token)
        )
        return await message.answer("Бот не инициализирован")

    match message.text:
        case ReplyCustomBotMenuKeyboard.Callback.ActionEnum.PARTNER_SHIP.value:
            bot_id = (await bot_db.get_bot_by_token(message.bot.token)).bot_id
            await message.answer(MessageTexts.CUSTOM_BOT_PARTNERSHIP.value,
                                 reply_markup=keyboards.get_partnership_inline_kb(bot_id))
        case _:
            default_msg = await get_option("default_msg", message.bot.token)

            await message.answer(
                format_locales(default_msg, message.from_user, message.chat),
                reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(
                    bot.bot_id
                )
            )


@multi_bot_router.callback_query(lambda query: InlineOrderCancelKeyboard.callback_validator(query.data))
async def handle_order_callback(query: CallbackQuery):
    callback_data = InlineOrderCancelKeyboard.Callback.model_validate_json(query.data)
    user_id = query.from_user.id
    order_id = callback_data.order_id

    try:
        order = await order_db.get_order(order_id)
    except OrderNotFound:
        custom_bot_logger.warning(
            f"user_id={user_id}: unable to change the status of order_id={order_id}",
            extra=extra_params(user_id=user_id, order_id=order_id)
        )
        await query.answer("Ошибка при работе с заказом, возможно статус уже изменился", show_alert=True)
        return await query.message.edit_reply_markup(None)

    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_ORDER_STATUSES:
            await query.message.edit_reply_markup(
                reply_markup=InlineOrderCustomBotKeyboard.get_keyboard(order_id)
            )
        case callback_data.ActionEnum.CANCEL:
            if order.status == OrderStatusValues.CANCELLED:
                return await query.answer("Этот статус уже выставлен")
            order.status = OrderStatusValues.CANCELLED

            await order_db.update_order(order)

            products = [(await product_db.get_product(int(product_id)), product_item.amount, product_item.extra_options)
                        for product_id, product_item in order.items.items()]
            await query.message.edit_text(order.convert_to_notification_text(products=products), reply_markup=None)
            msg_id_data = PREV_ORDER_MSGS.get_data()

            for item_id, item in order.items.items():
                product = await product_db.get_product(item_id)
                product.count += item.amount
                await product_db.update_product(product)

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
                f"order_id={order}: is cancelled by custom_user with user_id={user_id}",
                extra=extra_params(user_id=user_id, order_id=order)
            )


@multi_bot_router.callback_query(lambda query: InlineOrderCustomBotKeyboard.callback_validator(query.data))
async def handle_order_callback(query: CallbackQuery, state: FSMContext):
    callback_data = InlineOrderCustomBotKeyboard.Callback.model_validate_json(query.data)
    state_data = await state.get_data()

    order_id = callback_data.order_id
    user_id = query.from_user.id

    try:
        order = await order_db.get_order(order_id)
    except OrderNotFound:
        custom_bot_logger.warning(
            f"user_id={user_id}: tried to ask the question regarding order by order_id={order_id} is not found",
            extra=extra_params(user_id=user_id, order_id=order_id)
        )
        await query.answer("Ошибка при работе с заказом, возможно заказ был удалён", show_alert=True)
        return await query.message.edit_reply_markup(None)

    match callback_data.a:
        case callback_data.ActionEnum.PRE_CANCEL:
            await query.message.edit_reply_markup(
                reply_markup=InlineOrderCancelKeyboard.get_keyboard(order_id)
            )
        case callback_data.ActionEnum.ASK_QUESTION:
            custom_bot_logger.info(
                f"user_id={user_id}: wants to ask the question regarding order by order_id={order_id}",
                extra=extra_params(user_id=user_id, order_id=order_id)
            )

            if not state_data:
                state_data = {"order_id": order.id}
            else:
                if "last_question_time" in state_data and time.time() - state_data['last_question_time'] < 1 * 60 * 60:
                    custom_bot_logger.info(
                        f"user_id={user_id}: too early for asking question about order_id={order.id}",
                        extra=extra_params(user_id=user_id, order_id=order.id)
                    )
                    return await query.answer(
                        "Вы уже задавали вопрос недавно, пожалуйста, попробуйте позже "
                        "(между вопросами должен пройти час)", show_alert=True
                    )
                state_data['order_id'] = order.id

            await query.message.answer(
                "Вы можете отправить свой вопрос по заказу, отправив любое сообщение боту",
                reply_markup=keyboards.get_back_keyboard()
            )
            await state.set_state(CustomUserStates.WAITING_FOR_QUESTION)
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
                        reply_markup=InlineOrderQuestionKeyboard.get_keyboard(
                            order_id=order_id,
                            msg_id=message.message_id,
                            chat_id=message.chat.id
                        ))


@multi_bot_router.callback_query(lambda query: InlineOrderQuestionKeyboard.callback_validator(query.data))
async def ask_question_callback(query: CallbackQuery, state: FSMContext):
    callback_data = InlineOrderQuestionKeyboard.Callback.model_validate_json(
        query.data
    )
    state_data = await state.get_data()

    order_id = callback_data.order_id
    user_id = query.from_user.id
    bot_data = await bot_db.get_bot_by_token(query.bot.token)

    match callback_data.a:
        case callback_data.ActionEnum.APPROVE:
            if not state_data or 'order_id' not in state_data:
                custom_bot_logger.error(
                    f"user_id={user_id}: unable to approve question due to lost order_id={order_id} from state_data",
                    extra=extra_params(user_id=user_id, order_id=order_id)
                )

                await state.set_state(CustomUserStates.MAIN_MENU)
                await query.message.edit_reply_markup(None)
                return await query.answer("Произошла ошибка возвращаюсь в главное меню...", show_alert=True)

            try:
                order = await order_db.get_order(order_id)
            except OrderNotFound:
                custom_bot_logger.warning(
                    f"user_id={user_id}: unable to approve question due to lost order_id={order_id} from db",
                    extra=extra_params(user_id=user_id, order_id=order_id)
                )
                await query.answer("Ошибка при работе с заказом, возможно заказ был удалён", show_alert=True)
                return await query.message.edit_reply_markup(None)

            try:
                message = await main_bot.send_message(chat_id=bot_data.created_by,
                                                      text=f"Новый вопрос по заказу <b>#{order.id}</b> от пользователя "
                                                           f"<b>{'@' + query.from_user.username if query.from_user.username else query.from_user.full_name}</b> 👇\n\n"
                                                           f"<i>{query.message.reply_to_message.text}</i>\n\n"
                                                           f"Для ответа на вопрос <b>зажмите это сообщение</b> и ответьте на него")
                question_messages_data = QUESTION_MESSAGES.get_data()
                question_messages_data[message.message_id] = {
                    "question_from_custom_bot_message_id": callback_data.msg_id,
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

        case callback_data.a.CANCEL:
            cancel_text = "Отправка вопроса администратору отменена"
            await query.answer(
                cancel_text, show_alert=True
            )
            await query.message.answer(
                cancel_text,
                reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(bot_data.bot_id)
            )
            await query.message.edit_reply_markup(reply_markup=None)

            await state.set_state(CustomUserStates.MAIN_MENU)


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
