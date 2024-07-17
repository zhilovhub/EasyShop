import time

from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext

from custom_bots.multibot import main_bot, CustomUserStates, QUESTION_MESSAGES
from custom_bots.handlers.routers import multi_bot_router
from custom_bots.keyboards.question_keyboards import InlineOrderQuestionKeyboard, ReplyBackQuestionMenuKeyboard
from custom_bots.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard
from custom_bots.utils.question_utils import is_able_to_ask

from database.config import bot_db, order_db
from database.models.order_model import OrderNotFound

from logs.config import custom_bot_logger, extra_params


@multi_bot_router.message(CustomUserStates.WAITING_FOR_QUESTION)
async def handle_waiting_for_question_state(message: Message, state: FSMContext):
    state_data = await state.get_data()

    user_id = message.from_user.id
    bot_data = await bot_db.get_bot_by_token(message.bot.token)

    match message.text:
        case ReplyBackQuestionMenuKeyboard.Callback.ActionEnum.BACK_TO_MAIN_MENU.value:
            await message.answer(
                "Возвращаюсь в главное меню...",
                reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(bot_data.bot_id)
            )
        case _:
            if not state_data or 'order_id' not in state_data:
                custom_bot_logger.error(
                    f"user_id={user_id}: unable to accept a question due to lost order_id from state_data",
                    extra=extra_params(user_id=user_id)
                )
                raise Exception(f"user_id={user_id}: unable to accept a question due to lost order_id from state_data")

            order_id = state_data['order_id']

            await message.reply(
                f"Вы уверены что хотите отправить это сообщение вопросом к заказу "
                f"<b>#{order_id}</b>?",
                reply_markup=InlineOrderQuestionKeyboard.get_keyboard(
                    order_id=order_id,
                    msg_id=message.message_id,
                    chat_id=message.chat.id
                ))
            await message.answer(
                f"\n\nПосле отправки вопроса, Вы сможете отправить следующий <b>минимум через 1 час</b> или "
                f"<b>после ответа администратора</b>",
                reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(bot_data.bot_id)
            )

    await state.set_state(CustomUserStates.MAIN_MENU)
    await state.set_data(state_data)


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
            try:
                order = await order_db.get_order(order_id)
            except OrderNotFound as e:
                custom_bot_logger.warning(
                    f"user_id={user_id}: unable to approve question due to lost order_id={order_id} from db",
                    extra=extra_params(user_id=user_id, order_id=order_id),
                    exc_info=e
                )
                await query.answer("Заказ удалён администратором", show_alert=True)
                return await query.message.edit_reply_markup(None)

            try:
                if not await is_able_to_ask(query, state_data, user_id, order_id):
                    return

                message = await main_bot.send_message(
                    chat_id=bot_data.created_by,
                    text=f"Новый вопрос по заказу <b>#{order_id}</b> от пользователя "
                         f"<b>"
                         f"{'@' + query.from_user.username if query.from_user.username else query.from_user.full_name}"
                         f"</b> 👇\n\n"
                         f"<i>{query.message.reply_to_message.text}</i>\n\n"
                         f"Для ответа на вопрос <b>зажмите это сообщение</b> и ответьте на него")

                question_messages_data = QUESTION_MESSAGES.get_data()
                question_messages_data[message.message_id] = {
                    "question_from_custom_bot_message_id": callback_data.msg_id,
                    "order_id": order_id
                }

                QUESTION_MESSAGES.update_data(question_messages_data)

                custom_bot_logger.info(
                    f"user_id={bot_data.created_by}: got question regarded to order_id={order.id} "
                    f"from user_id={user_id}",
                    extra=extra_params(user_id=bot_data.created_by, order_id=order.id)
                )

            except TelegramAPIError as e:
                await main_bot.send_message(
                    chat_id=bot_data.created_by,
                    text="Вам поступило новое <b>сообщение-вопрос</b> от клиента, "
                         "но Вашему боту <b>не удалось Вам его отправить</b>, "
                         "проверьте писали ли Вы хоть раз своему боту и не заблокировали ли вы его"
                         f"\n\n* ссылка на Вашего бота @{(await query.bot.get_me()).username}")

                custom_bot_logger.error(
                    f"user_id={bot_data.created_by}: couldn't get question regarded to "
                    f"order_id={order.id} from user_id={user_id}",
                    extra=extra_params(user_id=bot_data.created_by, order_id=order_id),
                    exc_info=e
                )

                await state.set_state(CustomUserStates.MAIN_MENU)
                return await query.answer(
                    "Не удалось отправить Ваш вопрос. Администраторы уже уведомлены",
                    show_alert=True
                )

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
