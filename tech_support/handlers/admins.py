from datetime import datetime

from common_utils.keyboards.remove_keyboard import OurReplyKeyboardRemove

from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from tech_support.bot import bot, ADMIN_MESSAGES
from tech_support.utils.states import AdminStates
from tech_support.handlers.routers import admins_router
from tech_support.keyboards.keyboards import AnswerKeyboard, ReplyCancelKeyboard, AnswerUserButton
from tech_support.utils.message_texts import MessageTexts as TechMessageTexts


@admins_router.callback_query(lambda query: AnswerKeyboard.callback_validator(query.data))
async def handle_answer_question(query: CallbackQuery, state: FSMContext):
    lang = "ru"
    callback_data = AnswerKeyboard.Callback.model_validate_json(query.data)

    match callback_data.a:
        case callback_data.ActionEnum.ANSWER:
            messages_data = ADMIN_MESSAGES.get_data()
            await state.set_state(AdminStates.ANSWER_MESSAGE_TO_USER)
            await state.set_data({"user_id": callback_data.user_id, "msg_id": callback_data.msg_id})
            await query.message.answer(
                "Отправьте сообщение-ответ клиенту.", reply_markup=ReplyCancelKeyboard.get_keyboard(lang)
            )
            if f"{callback_data.user_id}#{callback_data.msg_id}" in messages_data:
                for admin, msg_id in messages_data[f"{callback_data.user_id}#{callback_data.msg_id}"]:
                    await bot.edit_message_text(
                        chat_id=admin,
                        message_id=msg_id,
                        text=query.message.reply_to_message.text
                        + f"\n\n[{datetime.now().strftime('%d.%m.%y %H:%M:%S')}] "
                        f"@{query.from_user.username} начал отвечать клиенту.",
                    )
            else:
                await query.message.reply_to_message.edit_text(
                    query.message.reply_to_message.text + f"\n\n[{datetime.now().strftime('%d.%m.%y %H:%M:%S')}] "
                    f"@{query.from_user.username} начал отвечать клиенту."
                )
            await query.answer()


@admins_router.message(AdminStates.ANSWER_MESSAGE_TO_USER)
async def handle_answer_to_user(message: Message, state: FSMContext):
    lang = "ru"
    if message.text:
        match message.text:
            case (
                ReplyCancelKeyboard.Callback.ActionEnum.CANCEL.value
                | ReplyCancelKeyboard.Callback.ActionEnum.CANCEL_ENG.value
            ):
                await message.answer(
                    **TechMessageTexts.get_canceled_sending_message_text(lang).as_kwargs(),
                    reply_markup=OurReplyKeyboardRemove(),
                )
                await state.clear()
                return
    state_data = await state.get_data()
    await bot.send_message(
        chat_id=state_data["user_id"], **TechMessageTexts.get_response_message_text(lang).as_kwargs()
    )
    await bot.copy_message(
        chat_id=state_data["user_id"],
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=AnswerUserButton.get_keyboard(lang),
    )
    await message.reply("Сообщение отправлено клиенту", reply_markup=OurReplyKeyboardRemove())
    await state.clear()
