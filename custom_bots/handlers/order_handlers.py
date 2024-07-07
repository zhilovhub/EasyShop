import time

from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.main import product_review_db
from bot.exceptions.exceptions import BotNotFound
from bot.keyboards.question_keyboards import ReplyBackQuestionMenuKeyboard
from bot.keyboards.order_manage_keyboards import InlineOrderCancelKeyboard, \
    InlineOrderCustomBotKeyboard, InlineCreateReviewKeyboard, ReplyGetReviewMarkKeyboard, ReplyReviewBackKeyboard, \
    InlinePickReviewProductKeyboard
from bot.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard

from custom_bots.multibot import order_db, product_db, main_bot, PREV_ORDER_MSGS, CustomUserStates, bot_db
from custom_bots.handlers.routers import multi_bot_router

from database.models.order_model import OrderStatusValues, OrderNotFound
from database.models.product_review_model import ProductReviewSchemaWithoutID

from logs.config import custom_bot_logger, extra_params


@multi_bot_router.callback_query(lambda query: InlineOrderCancelKeyboard.callback_validator(query.data))
async def handle_cancel_order_callback(query: CallbackQuery):
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
                reply_markup=ReplyBackQuestionMenuKeyboard.get_keyboard()
            )
            await state.set_state(CustomUserStates.WAITING_FOR_QUESTION)
            await state.set_data(state_data)


@multi_bot_router.callback_query(lambda query: InlineCreateReviewKeyboard.callback_validator(query.data))
async def create_order_review(query: CallbackQuery, state: FSMContext):
    callback_data = InlineCreateReviewKeyboard.Callback.model_validate_json(query.data)
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
        case callback_data.ActionEnum.CREATE_REVIEW:
            await query.message.answer(text="Выберите товар 🪧", reply_markup=await InlinePickReviewProductKeyboard.get_keyboard(order.items))
            await query.answer()
            await state.set_state(CustomUserStates.WAITING_FOR_REVIEW_PRODUCT)


@multi_bot_router.callback_query(StateFilter(CustomUserStates.WAITING_FOR_REVIEW_PRODUCT))
async def get_product_id(query: CallbackQuery, state: FSMContext):
    callback_data = InlinePickReviewProductKeyboard.Callback.model_validate_json(query.data)
    state_data = await state.get_data()
    match callback_data.a:
        case callback_data.ActionEnum.PICK_PRODUCT:
            product = await product_review_db.get_product_review_by_user_id_and_product_id(
                user_id=query.from_user.id, product_id=callback_data.product_id)
            if product:
                try:
                    bot = await bot_db.get_bot_by_token(query.message.bot.token)
                except BotNotFound:
                    custom_bot_logger.warning(
                        f"bot_token={query.message.bot.token}: this bot is not in db",
                        extra=extra_params(bot_token=query.message.bot.token)
                    )
                    await query.message.answer("Бот не инициализирован")
                await query.message.answer("Вы уже оставили отзыв на этот продукт!", reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(bot.bot_id))
                await state.clear()
                return
            await query.message.answer(text="Оцените качество товаров ✔️", reply_markup=ReplyGetReviewMarkKeyboard.get_keyboard())
            await query.answer()
            await state.set_state(CustomUserStates.WAITING_FOR_REVIEW_MARK)
            await state.set_data({
                "product_id": callback_data.product_id
            })


@multi_bot_router.message(StateFilter(CustomUserStates.WAITING_FOR_REVIEW_MARK))
async def get_review_mark(message: Message, state: FSMContext):
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
    except BotNotFound:
        custom_bot_logger.warning(
            f"bot_token={message.bot.token}: this bot is not in db",
            extra=extra_params(bot_token=message.bot.token)
        )
        return await message.answer("Бот не инициализирован")
    if message.text == "Назад 🔙":
        return message.answer("Отправка отзыва отменена ✖️", reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(bot.bot_id))
    mark_value = 0
    state_data = await state.get_data()
    match message.text:
        case ReplyGetReviewMarkKeyboard.Callback.ActionEnum.ONE.value:
            mark_value = 1
        case ReplyGetReviewMarkKeyboard.Callback.ActionEnum.TWO.value:
            mark_value = 2
        case ReplyGetReviewMarkKeyboard.Callback.ActionEnum.THREE.value:
            mark_value = 3
        case ReplyGetReviewMarkKeyboard.Callback.ActionEnum.FOUR.value:
            mark_value = 4
        case ReplyGetReviewMarkKeyboard.Callback.ActionEnum.FIVE.value:
            mark_value = 5
        case _:
            return await message.answer("Чтобы оставить оценку, нажмите на кнопку ниже 👇")

    await state.set_state(CustomUserStates.WAITING_FOR_REVIEW_TEXT)
    await state.set_data({
        "product_id": state_data["product_id"],
        "mark": mark_value,
    })
    await message.answer("Напишите комментарий к вашему отзыву 📨", reply_markup=ReplyReviewBackKeyboard.get_keyboard())


@multi_bot_router.message(StateFilter(CustomUserStates.WAITING_FOR_REVIEW_TEXT))
async def get_review_text(message: Message, state: FSMContext):
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
    except BotNotFound:
        custom_bot_logger.warning(
            f"bot_token={message.bot.token}: this bot is not in db",
            extra=extra_params(bot_token=message.bot.token)
        )
        return await message.answer("Бот не инициализирован")
    if message.text == "Назад 🔙":
        return message.answer("Отправка отзыва отменена ✖️", reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(bot.bot_id))
    state_data = await state.get_data()
    mark = state_data["mark"]
    await product_review_db.add_product_review(
        ProductReviewSchemaWithoutID(
            bot_id=bot.bot_id,
            product_id=state_data["product_id"],
            mark=mark,
            review_text=message.text,
            user_id=message.from_user.id
        )
    )
    await message.answer("Спасибо за отзыв 📬", reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(bot.bot_id))
    await state.clear()
