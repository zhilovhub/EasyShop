from aiogram.filters import CommandStart, Command
from aiogram.types import Message, User, CallbackQuery
from aiogram.fsm.context import FSMContext

from common_utils.keyboards.remove_keyboard import OurReplyKeyboardRemove

from tech_support.bot import bot
from tech_support.utils.states import UserStates
from tech_support.handlers.routers import users_router
from tech_support.keyboards.keyboards import MainUserKeyboard, FAQKeyboard, ReplyCancelKeyboard
from tech_support.utils.message_texts import MessageTexts as TechMessageTexts
from tech_support.utils.send_messages import send_message_to_admins


@users_router.callback_query(lambda query: MainUserKeyboard.callback_validator(query.data))
async def manage_main_callback(query: CallbackQuery, state: FSMContext):
    callback_data = MainUserKeyboard.Callback.model_validate_json(query.data)
    # TODO get lang from db (translate_shop branch)
    lang = "ru"

    match callback_data.a:
        case callback_data.ActionEnum.FAQ:
            await _output_faq(query.from_user, lang, state)
            await query.answer()
        case callback_data.ActionEnum.ASK_QUESTION:
            await query.message.answer(
                **TechMessageTexts.get_ask_question_message_text(lang).as_kwargs(),
                reply_markup=ReplyCancelKeyboard.get_keyboard(lang),
            )
            await state.set_state(UserStates.SEND_QUESTION_TO_ADMINS)
            await query.answer()
        case callback_data.ActionEnum.SUGGEST:
            await query.message.answer(
                **TechMessageTexts.get_suggest_update_message_text(lang).as_kwargs(),
                reply_markup=ReplyCancelKeyboard.get_keyboard(lang),
            )
            await state.set_state(UserStates.SEND_SUGGESTION_TO_ADMIN)
            await query.answer()


@users_router.callback_query(lambda query: FAQKeyboard.callback_validator(query.data))
async def faq_callback(query: CallbackQuery):
    callback_data = FAQKeyboard.Callback.model_validate_json(query.data)
    # TODO get lang from db (translate_shop branch)
    lang = "ru"

    match callback_data.a:
        case callback_data.ActionEnum.PAYMENT:
            await query.message.answer(**TechMessageTexts.get_payment_faq_message_text(lang).as_kwargs())
            await query.answer()
        case callback_data.ActionEnum.ADMINS:
            await query.message.answer(**TechMessageTexts.get_admins_faq_message_text(lang).as_kwargs())
            await query.answer()
        case callback_data.ActionEnum.RESTRICTIONS:
            await query.message.answer(**TechMessageTexts.get_restrictions_faq_message_text(lang).as_kwargs())
            await query.answer()
        case callback_data.ActionEnum.CUSTOMIZATION:
            await query.message.answer(**TechMessageTexts.get_customization_faq_message_text(lang).as_kwargs())
            await query.answer()
        case callback_data.ActionEnum.EXPORT_PRODUCT:
            await query.message.answer(**TechMessageTexts.get_export_faq_message_text(lang).as_kwargs())
            await query.answer()


@users_router.message(CommandStart())
async def start_cmd_handler(message: Message):
    # TODO get lang from db (translate_shop branch)
    lang = "ru"
    await message.answer(
        **TechMessageTexts.get_start_message_text(lang).as_kwargs(), reply_markup=MainUserKeyboard.get_keyboard(lang)
    )


async def _output_faq(user: User, lang: str, state: FSMContext):
    # TODO replace lang to lang enum from db (translate_shop branch)
    if await state.get_state():
        await bot.send_message(
            chat_id=user.id,
            **TechMessageTexts.get_canceled_sending_message_text(lang).as_kwargs(),
            reply_markup=OurReplyKeyboardRemove(),
        )
        await state.clear()
    await bot.send_message(
        chat_id=user.id,
        **TechMessageTexts.get_faq_message_text(lang).as_kwargs(),
        reply_markup=FAQKeyboard.get_keyboard(lang),
    )


@users_router.message(Command("faq"))
async def faq_cmd_handler(message: Message, state: FSMContext):
    # TODO get lang from db (translate_shop branch)
    lang = "ru"
    await _output_faq(message.from_user, lang, state)


@users_router.message(UserStates.SEND_SUGGESTION_TO_ADMIN)
async def handle_sending_suggestion_to_admins(message: Message, state: FSMContext):
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
    await send_message_to_admins(message, lang, suggest=True)
    await state.clear()


@users_router.message(UserStates.SEND_QUESTION_TO_ADMINS)
async def handle_sending_question_to_admins(message: Message, state: FSMContext):
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
    await send_message_to_admins(message, lang, suggest=False)
    await state.clear()
