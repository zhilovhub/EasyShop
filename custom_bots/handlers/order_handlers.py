from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from custom_bots.multibot import main_bot, PREV_ORDER_MSGS, CustomUserStates
from custom_bots.handlers.routers import multi_bot_router
from custom_bots.utils.custom_message_texts import CustomMessageTexts
from custom_bots.keyboards.question_keyboards import ReplyBackQuestionMenuKeyboard
from custom_bots.keyboards.order_manage_keyboards import (
    InlinePickReviewProductKeyboard,
    ReplyGetReviewMarkKeyboard,
    ReplyReviewBackKeyboard,
)
from custom_bots.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard

from custom_bots.utils.question_utils import is_able_to_ask
from common_utils.keyboards.order_manage_keyboards import (
    InlineOrderCancelKeyboard,
    InlineOrderCustomBotKeyboard,
    InlineCreateReviewKeyboard,
    InlineAcceptReviewKeyboard,
)
from common_utils.message_texts import MessageTexts as CommonMessageTexts

from database.config import product_review_db, order_db, product_db, bot_db, custom_bot_user_db
from database.enums import UserLanguageValues
from database.models.bot_model import BotNotFoundError
from database.models.order_model import OrderStatusValues, OrderNotFoundError
from database.models.product_model import ProductNotFoundError
from database.models.product_review_model import ProductReviewSchemaWithoutID, ProductReviewNotFoundError

from logs.config import custom_bot_logger, extra_params


@multi_bot_router.callback_query(lambda query: InlineOrderCancelKeyboard.callback_validator(query.data))
async def handle_cancel_order_callback(query: CallbackQuery):
    callback_data = InlineOrderCancelKeyboard.Callback.model_validate_json(query.data)
    user_id = query.from_user.id
    order_id = callback_data.order_id
    lang = UserLanguageValues.ENGLISH

    try:
        order = await order_db.get_order(order_id)
        custom_bot_user = await custom_bot_user_db.get_custom_bot_user(order.bot_id, user_id)
        lang = custom_bot_user.user_language
    except OrderNotFoundError:
        custom_bot_logger.warning(
            f"user_id={user_id}: unable to change the status of order_id={order_id}",
            extra=extra_params(user_id=user_id, order_id=order_id),
        )
        await query.answer(CustomMessageTexts.get_order_change_err_message(lang), show_alert=True)
        return await query.message.edit_reply_markup(None)

    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_ORDER_STATUSES:
            await query.message.edit_reply_markup(
                reply_markup=InlineOrderCustomBotKeyboard.get_keyboard(order_id, lang=custom_bot_user.user_language)
            )
        case callback_data.ActionEnum.CANCEL:
            if order.status == OrderStatusValues.CANCELLED:
                return await query.answer(CustomMessageTexts.get_status_already_err_message(lang))
            order.status = OrderStatusValues.CANCELLED

            await order_db.update_order(order)

            products = [
                (await product_db.get_product(int(product_id)), product_item.amount, product_item.used_extra_options)
                for product_id, product_item in order.items.items()
            ]
            # await query.message.edit_text(order.convert_to_notification_text(products=products), reply_markup=None)
            text = await CommonMessageTexts.generate_order_notification_text(order, products, lang=lang)
            await query.message.edit_text(**text, reply_markup=None)
            msg_id_data = PREV_ORDER_MSGS.get_data()

            for item_id, item in order.items.items():
                product = await product_db.get_product(item_id)
                product.count += item.amount
                await product_db.update_product(product)

            text = await CommonMessageTexts.generate_order_notification_text(
                order=order,
                products=products,
                username="@" + query.from_user.username if query.from_user.username else query.from_user.full_name,
                is_admin=True,
            )

            await main_bot.edit_message_text(
                **text,
                chat_id=msg_id_data[order_id][0],
                message_id=msg_id_data[order_id][1],
                reply_markup=None,
            )
            await main_bot.send_message(
                chat_id=msg_id_data[order_id][0],
                text=f"Новый статус заказа <b>#{order_id}</b>\n<b>{order.translate_order_status(lang)}</b>",
            )

            del msg_id_data[order_id]

            custom_bot_logger.info(
                f"order_id={order}: is cancelled by custom_user with user_id={user_id}",
                extra=extra_params(user_id=user_id, order_id=order),
            )


@multi_bot_router.callback_query(lambda query: InlineOrderCustomBotKeyboard.callback_validator(query.data))
async def handle_order_callback(query: CallbackQuery, state: FSMContext):
    callback_data = InlineOrderCustomBotKeyboard.Callback.model_validate_json(query.data)
    state_data = await state.get_data()

    order_id = callback_data.order_id
    user_id = query.from_user.id
    lang = UserLanguageValues.ENGLISH

    try:
        order = await order_db.get_order(order_id)
        custom_bot_user = await custom_bot_user_db.get_custom_bot_user(order.bot_id, user_id)
        lang = custom_bot_user.user_language
    except OrderNotFoundError:
        custom_bot_logger.warning(
            f"user_id={user_id}: tried to ask the question regarding order by order_id={order_id} is not found",
            extra=extra_params(user_id=user_id, order_id=order_id),
        )
        await query.answer(CustomMessageTexts.get_order_change_maybe_deleted_err_message(lang), show_alert=True)
        return await query.message.edit_reply_markup(None)

    match callback_data.a:
        case callback_data.ActionEnum.PRE_CANCEL:
            await query.message.edit_reply_markup(
                reply_markup=InlineOrderCancelKeyboard.get_keyboard(order_id, lang=lang)
            )
        case callback_data.ActionEnum.ASK_QUESTION:
            custom_bot_logger.info(
                f"user_id={user_id}: wants to ask the question regarding order by order_id={order_id}",
                extra=extra_params(user_id=user_id, order_id=order_id),
            )

            if not state_data:
                state_data = {"order_id": order_id}
            else:
                if not await is_able_to_ask(query, state_data, user_id, order_id):
                    return
                state_data["order_id"] = order_id

            await query.answer()
            await query.message.answer(
                **CustomMessageTexts.get_ask_question_message(lang).as_kwargs(),
                reply_markup=ReplyBackQuestionMenuKeyboard.get_keyboard(custom_bot_user.user_language),
            )
            await state.set_state(CustomUserStates.WAITING_FOR_QUESTION)
            await state.set_data(state_data)


@multi_bot_router.callback_query(lambda query: InlineCreateReviewKeyboard.callback_validator(query.data))
async def create_order_review(query: CallbackQuery):
    callback_data = InlineCreateReviewKeyboard.Callback.model_validate_json(query.data)
    order_id = callback_data.order_id
    user_id = query.from_user.id
    lang = UserLanguageValues.ENGLISH
    try:
        order = await order_db.get_order(order_id)
        custom_bot_user = await custom_bot_user_db.get_custom_bot_user(order.bot_id, user_id)
        lang = custom_bot_user.user_language
    except OrderNotFoundError:
        custom_bot_logger.warning(
            f"user_id={user_id}: tried to tried to create reviw to order_id={order_id} is not found",
            extra=extra_params(user_id=user_id, order_id=order_id),
        )
        await query.answer(CustomMessageTexts.get_order_change_maybe_deleted_err_message(lang), show_alert=True)
        return await query.message.edit_reply_markup(None)
    match callback_data.a:
        case callback_data.ActionEnum.CREATE_REVIEW:
            await query.message.edit_text(
                **CustomMessageTexts.get_select_product_message(lang).as_kwargs(),
                reply_markup=await InlinePickReviewProductKeyboard.get_keyboard(order.items),
            )
            await query.answer()


@multi_bot_router.callback_query(lambda query: InlinePickReviewProductKeyboard.callback_validator(query.data))
async def get_product_id(query: CallbackQuery, state: FSMContext):
    callback_data = InlinePickReviewProductKeyboard.Callback.model_validate_json(query.data)
    lang = UserLanguageValues.RUSSIAN
    match callback_data.a:
        case callback_data.ActionEnum.PICK_PRODUCT:
            try:
                bot = await bot_db.get_bot_by_token(query.message.bot.token)
                custom_bot_user = await custom_bot_user_db.get_custom_bot_user(bot.bot_id, query.from_user.id)
                lang = custom_bot_user.user_language
            except BotNotFoundError:
                custom_bot_logger.warning(
                    f"bot_token={query.message.bot.token}: this bot is not in db",
                    extra=extra_params(bot_token=query.message.bot.token),
                )
                return await query.message.answer(**CustomMessageTexts.get_bot_not_init_message(lang).as_kwargs())
            try:
                await product_review_db.get_product_review_by_user_id_and_product_id(
                    user_id=query.from_user.id, product_id=callback_data.product_id
                )

                await query.answer(CustomMessageTexts.get_review_already_err_message(lang), show_alert=True)
                await state.set_state(CustomUserStates.MAIN_MENU)
                return
            except ProductReviewNotFoundError:
                await query.message.answer(
                    **CustomMessageTexts.get_review_product_message(lang).as_kwargs(),
                    reply_markup=ReplyGetReviewMarkKeyboard.get_keyboard(lang),
                )
                await query.answer()

                await state.set_state(CustomUserStates.WAITING_FOR_REVIEW_MARK)
                await state.set_data({"product_id": callback_data.product_id})


@multi_bot_router.message(StateFilter(CustomUserStates.WAITING_FOR_REVIEW_MARK))
async def get_review_mark(message: Message, state: FSMContext):
    lang = UserLanguageValues.RUSSIAN

    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
        custom_bot_user = await custom_bot_user_db.get_custom_bot_user(bot.bot_id, message.from_user.id)
        lang = custom_bot_user.user_language
    except BotNotFoundError:
        custom_bot_logger.warning(
            f"bot_token={message.bot.token}: this bot is not in db", extra=extra_params(bot_token=message.bot.token)
        )
        return await message.answer(**CustomMessageTexts.get_bot_not_init_message(lang).as_kwargs())

    actions = ReplyReviewBackKeyboard.Callback.ActionEnum
    if message.text in (actions.BACK.value, actions.BACK_ENG.value, actions.BACK_HEB.value):
        await state.set_state(CustomUserStates.MAIN_MENU)
        return message.answer(
            **CustomMessageTexts.get_send_review_canceled_message(lang).as_kwargs(),
            reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(lang),
        )

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
            return await message.answer(**CustomMessageTexts.get_review_score_message(lang).as_kwargs())

    await state.set_state(CustomUserStates.WAITING_FOR_REVIEW_TEXT)
    await state.set_data(
        {
            "product_id": state_data["product_id"],
            "mark": mark_value,
        }
    )
    await message.answer(
        **CustomMessageTexts.get_review_comment_message(lang).as_kwargs(),
        reply_markup=ReplyReviewBackKeyboard.get_keyboard(lang),
    )


@multi_bot_router.message(StateFilter(CustomUserStates.WAITING_FOR_REVIEW_TEXT))
async def get_review_text(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = UserLanguageValues.RUSSIAN
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
        custom_bot_user = await custom_bot_user_db.get_custom_bot_user(bot.bot_id, message.from_user.id)
        lang = custom_bot_user.user_language
    except BotNotFoundError:
        custom_bot_logger.warning(
            f"bot_token={message.bot.token}: this bot is not in db", extra=extra_params(bot_token=message.bot.token)
        )
        return await message.answer(**CustomMessageTexts.get_shop_button_message(lang).as_kwargs())
    actions = ReplyReviewBackKeyboard.Callback.ActionEnum
    if message.text in (actions.BACK.value, actions.BACK_ENG.value, actions.BACK_HEB.value):
        await state.set_state(CustomUserStates.WAITING_FOR_REVIEW_MARK)
        await state.set_data({"product_id": state_data["product_id"]})
        return message.answer(
            **CustomMessageTexts.get_review_score_message(lang).as_kwargs(),
            reply_markup=ReplyGetReviewMarkKeyboard.get_keyboard(lang),
        )

    state_data = await state.get_data()
    mark = state_data["mark"]
    review_id = await product_review_db.add_product_review(
        ProductReviewSchemaWithoutID(
            bot_id=bot.bot_id,
            product_id=state_data["product_id"],
            mark=mark,
            review_text=message.text,
            user_id=message.from_user.id,
        )
    )
    await message.answer(
        **CustomMessageTexts.get_review_thx_message(lang).as_kwargs(),
        reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(lang),
    )
    try:
        product = await product_db.get_product(state_data["product_id"])
        await main_bot.send_message(
            chat_id=bot.created_by,
            text=CustomMessageTexts.show_product_review_info(mark, message.text, product.name),
            reply_markup=InlineAcceptReviewKeyboard.get_keyboard(review_id),
        )
        await state.set_state(CustomUserStates.MAIN_MENU)
    except ProductNotFoundError:
        pass
