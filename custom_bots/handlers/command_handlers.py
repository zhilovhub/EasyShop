from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, CommandObject, Command

from custom_bots.multibot import CustomUserStates
from custom_bots.utils.utils import format_locales
from custom_bots.handlers.routers import multi_bot_router, multi_bot_raw_router
from custom_bots.utils.custom_message_texts import CustomMessageTexts
from custom_bots.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard, InlineSelectLanguageKb

from common_utils.bot_utils import create_bot_options
from common_utils.keyboards.keyboards import (
    InlineCustomBotModeProductKeyboardButton,
    InlineBotMainWebAppButton,
    FirstTimeInlineSelectLanguageKb,
)
from common_utils.exceptions.bot_exceptions import UnknownDeepLinkArgument
from common_utils.broadcasting.broadcasting import send_event, EventTypes

from database.config import custom_bot_user_db, bot_db, option_db, pickle_store_db
from database.enums.language import get_lang_emoji
from database.models.bot_model import BotNotFoundError
from database.models.option_model import OptionNotFoundError
from database.models.custom_bot_user_model import CustomBotUserNotFoundError

from database.enums import UserLanguageValues
from database.models.pickle_storage_model import PickledDataNotFound

from logs.config import custom_bot_logger, extra_params


async def _check_new_user(event: Message | CallbackQuery, user_id: int):
    try:
        db_bot = await bot_db.get_bot_by_token(event.bot.token)
        custom_bot_logger.info(
            f"user_id={user_id}: user called /start at bot_id={db_bot.bot_id}",
            extra=extra_params(user_id=user_id, bot_id=db_bot.bot_id),
        )

        try:
            await custom_bot_user_db.get_custom_bot_user(db_bot.bot_id, user_id)
        except CustomBotUserNotFoundError:
            custom_bot_logger.info(
                f"user_id={user_id}: user not found in database, trying to add to it",
                extra=extra_params(user_id=user_id, bot_id=db_bot.bot_id),
            )

            await custom_bot_user_db.add_custom_bot_user(db_bot.bot_id, user_id)
            if user_id == db_bot.created_by:
                await send_event(event.from_user, EventTypes.FIRST_ADMIN_MESSAGE, event_bot=event.bot)
            else:
                await send_event(event.from_user, EventTypes.FIRST_USER_MESSAGE, event_bot=event.bot)
    except BotNotFoundError as e:
        custom_bot_logger.warning("Bot not initialized", exc_info=e)
        await Bot(event.bot.token).delete_webhook()
        return await event.answer(**CustomMessageTexts.get_bot_not_init_message(UserLanguageValues.ENGLISH).as_kwargs())


@multi_bot_raw_router.callback_query(lambda query: FirstTimeInlineSelectLanguageKb.callback_validator(query.data))
async def first_language_select_handler(query: CallbackQuery, **kwargs):
    callback_data = FirstTimeInlineSelectLanguageKb.Callback.model_validate_json(query.data)

    object_uuid = callback_data.id
    selected_lang = callback_data.s

    try:
        pickled_object = await pickle_store_db.get_pickled_object(object_uuid)
        pickled_callable = pickled_object.unpickle_callable()
        pickled_data = pickled_object.unpickle_args()
    except PickledDataNotFound:
        custom_bot_logger.debug(f"pickled handler with id: {object_uuid} bot found in database")
        await query.answer("Not actual data", show_alert=True)
        await query.message.edit_reply_markup(reply_markup=None)
        return

    await _check_new_user(query, query.from_user.id)

    db_bot = await bot_db.get_bot_by_token(query.bot.token)
    custom_bot_user = await custom_bot_user_db.get_custom_bot_user(db_bot.bot_id, query.from_user.id)

    match callback_data.a:
        case callback_data.ActionEnum.SELECT:
            custom_bot_user.user_language = selected_lang
            await custom_bot_user_db.update_custom_bot_user(custom_bot_user)
            lang_set_text = (
                CustomMessageTexts.get_lang_set(custom_bot_user.user_language)
                + f" {get_lang_emoji(custom_bot_user.user_language)}"
            )
            await query.answer(lang_set_text, show_alert=True)
            # Возвращение актуальных данных в хендлер
            pickled_data["data"]["event_from_user"] = kwargs["event_from_user"]
            pickled_data["data"]["event_chat"] = kwargs["event_chat"]
            pickled_data["data"]["session"] = kwargs["session"]
            pickled_data["data"]["bot"] = kwargs["bot"]
            pickled_data["data"]["fsm_storage"] = kwargs["fsm_storage"]
            pickled_data["data"]["state"] = kwargs["state"]

            # валидация типов, которые были задамплены
            for k, typ in pickled_data["data"]["to_validate"].items():
                pickled_data["data"][k] = typ.model_validate(pickled_data["data"][k])

            # установка выбранного языка
            pickled_data["data"]["lang"] = custom_bot_user.user_language

            # валидация эвента
            event = pickled_data["data"]["event_type_to_validate"](**pickled_data["event"])
            # добавление объекта бота к эвенту
            event = event.as_(bot=kwargs["bot"])

            await pickled_callable(event, pickled_data["data"])
            await pickle_store_db.delete_pickled_object(object_uuid)
            await query.message.edit_reply_markup(reply_markup=None)
            await query.message.edit_text(query.message.text + "\n\n" + lang_set_text)


@multi_bot_router.message(CommandStart(deep_link=True))
async def deep_link_start_handler(
    message: Message, state: FSMContext, command: CommandObject, lang: UserLanguageValues
):
    """
    :raises UnknownDeepLinkArgument:
    """
    deep_link_params = command.args.split()

    db_bot = await bot_db.get_bot_by_token(message.bot.token)
    # Проверяем, новый ли пользователь
    await _check_new_user(message, message.from_user.id)

    if deep_link_params[0].startswith("product_"):
        product_id = int(deep_link_params[0].strip().split("_")[-1])
        await state.set_state(CustomUserStates.MAIN_MENU)
        return await message.answer(
            **CustomMessageTexts.get_product_page_message(lang).as_kwargs(),
            reply_markup=InlineCustomBotModeProductKeyboardButton.get_keyboard(product_id, db_bot.bot_id),
        )
    elif deep_link_params[0] == "web_app":
        await state.set_state(CustomUserStates.MAIN_MENU)
        return await message.answer(
            **CustomMessageTexts.get_shop_page_message(lang).as_kwargs(),
            reply_markup=InlineBotMainWebAppButton.get_keyboard(db_bot.bot_id, lang),
        )
    else:
        raise UnknownDeepLinkArgument(arg=deep_link_params)


@multi_bot_router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext, lang: UserLanguageValues):
    user_id = message.from_user.id

    db_bot = await bot_db.get_bot_by_token(message.bot.token)

    await _check_new_user(message, user_id)

    try:
        options = await option_db.get_option(db_bot.options_id)
    except OptionNotFoundError:
        new_options_id = await create_bot_options()
        db_bot.options_id = new_options_id
        await bot_db.update_bot(db_bot)
        options = await option_db.get_option(new_options_id)
    start_msg = options.start_msg
    bot_data = await message.bot.get_me()
    await message.answer(
        format_locales(start_msg[lang.value], message.from_user, message.chat, bot_data=bot_data),
        reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(lang=lang),
    )
    await state.set_state(CustomUserStates.MAIN_MENU)


@multi_bot_router.message(Command("lang"))
async def lang_command_handler(message: Message, lang: UserLanguageValues):
    db_bot = await bot_db.get_bot_by_token(message.bot.token)
    bot_options = await option_db.get_option(db_bot.options_id)
    await message.answer(
        **CustomMessageTexts.get_select_language_message(lang).as_kwargs(),
        reply_markup=InlineSelectLanguageKb.get_keyboard(
            bot_id=db_bot.bot_id, languages=bot_options.languages, current_lang=lang
        ),
    )


@multi_bot_router.callback_query(lambda query: InlineSelectLanguageKb.callback_validator(query.data))
async def language_select_handler(query: CallbackQuery):
    callback_data = InlineSelectLanguageKb.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id
    selected_lang = callback_data.selected

    bot = await bot_db.get_bot(bot_id)
    bot_options = await option_db.get_option(bot.options_id)

    custom_bot_user = await custom_bot_user_db.get_custom_bot_user(bot_id, query.from_user.id)

    match callback_data.a:
        case callback_data.ActionEnum.SELECT:
            if selected_lang == custom_bot_user.user_language:
                return await query.answer(
                    CustomMessageTexts.get_lang_already_set(custom_bot_user.user_language), show_alert=True
                )
            custom_bot_user.user_language = selected_lang
            await custom_bot_user_db.update_custom_bot_user(custom_bot_user)
            await query.answer(CustomMessageTexts.get_lang_set(custom_bot_user.user_language), show_alert=True)
            await query.message.edit_text(
                **CustomMessageTexts.get_select_language_message(custom_bot_user.user_language).as_kwargs(),
                reply_markup=InlineSelectLanguageKb.get_keyboard(
                    bot_id, bot_options.languages, custom_bot_user.user_language
                ),
            )
