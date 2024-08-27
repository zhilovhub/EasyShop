from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, CommandObject

from custom_bots.multibot import CustomUserStates
from custom_bots.utils.utils import format_locales
from custom_bots.handlers.routers import multi_bot_router
from custom_bots.utils.custom_message_texts import CustomMessageTexts
from custom_bots.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard, InlineSelectLanguageKb

from common_utils.bot_utils import create_bot_options
from common_utils.keyboards.keyboards import InlineCustomBotModeProductKeyboardButton, InlineBotMainWebAppButton
from common_utils.exceptions.bot_exceptions import UnknownDeepLinkArgument
from common_utils.broadcasting.broadcasting import send_event, EventTypes

from database.config import custom_bot_user_db, bot_db, option_db
from database.models.bot_model import BotNotFoundError
from database.models.option_model import OptionNotFoundError
from database.models.custom_bot_user_model import CustomBotUserNotFoundError

from database.enums import UserLanguageValues

from logs.config import custom_bot_logger, extra_params


async def _check_new_user(message: Message, user_id: int):
    tg_user_lang = message.from_user.language_code
    match tg_user_lang:
        case "ru":
            lang = UserLanguageValues.RUSSIAN
        case "he":
            lang = UserLanguageValues.HEBREW
        case "en" | _:
            lang = UserLanguageValues.ENGLISH
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
        custom_bot_logger.info(
            f"user_id={user_id}: user called /start at bot_id={bot.bot_id}",
            extra=extra_params(user_id=user_id, bot_id=bot.bot_id),
        )
        custom_bot_logger.debug(
            f"new custom bot user {user_id} with tg language code : {tg_user_lang}, setting our lang : {lang}",
            extra=extra_params(bot_id=bot.bot_id, user_id=user_id),
        )

        try:
            await custom_bot_user_db.get_custom_bot_user(bot.bot_id, user_id)
        except CustomBotUserNotFoundError:
            custom_bot_logger.info(
                f"user_id={user_id}: user not found in database, trying to add to it",
                extra=extra_params(user_id=user_id, bot_id=bot.bot_id),
            )

            custom_bot_options = await option_db.get_option(bot.bot_id)
            if custom_bot_options.languages:
                if len(custom_bot_options.languages) > 1:
                    if lang not in custom_bot_options.languages:
                        lang = custom_bot_options.languages[0]
                    await message.answer(
                        **CustomMessageTexts.get_select_language_message(lang).as_kwargs(),
                        reply_markup=InlineSelectLanguageKb.get_keyboard(
                            bot_id=bot.bot_id,
                            languages=custom_bot_options.languages,
                            current_lang=lang,
                        ),
                    )
                else:
                    lang = custom_bot_options.languages[0]

            await custom_bot_user_db.add_custom_bot_user(bot.bot_id, user_id, lang=lang)
            if user_id == bot.created_by:
                await send_event(message.from_user, EventTypes.FIRST_ADMIN_MESSAGE, event_bot=message.bot)
            else:
                await send_event(message.from_user, EventTypes.FIRST_USER_MESSAGE, event_bot=message.bot)
    except BotNotFoundError as e:
        custom_bot_logger.warning("Bot not initialized", exc_info=e)
        await Bot(message.bot.token).delete_webhook()
        return await message.answer(**CustomMessageTexts.get_bot_not_init_message(lang).as_kwargs())


@multi_bot_router.message(CommandStart(deep_link=True))
async def deep_link_start_handler(message: Message, state: FSMContext, command: CommandObject):
    """
    :raises UnknownDeepLinkArgument:
    """
    deep_link_params = command.args.split()

    bot = await bot_db.get_bot_by_token(message.bot.token)
    # Проверяем, новый ли пользователь
    await _check_new_user(message, message.from_user.id)

    custom_bot_user = await custom_bot_user_db.get_custom_bot_user(bot.bot_id, message.from_user.id)

    if deep_link_params[0].startswith("product_"):
        product_id = int(deep_link_params[0].strip().split("_")[-1])
        await state.set_state(CustomUserStates.MAIN_MENU)
        return await message.answer(
            **CustomMessageTexts.get_product_page_message(custom_bot_user.user_language).as_kwargs(),
            reply_markup=InlineCustomBotModeProductKeyboardButton.get_keyboard(product_id, bot.bot_id),
        )
    elif deep_link_params[0] == "web_app":
        await state.set_state(CustomUserStates.MAIN_MENU)
        return await message.answer(
            **CustomMessageTexts.get_shop_page_message(custom_bot_user.user_language).as_kwargs(),
            reply_markup=InlineBotMainWebAppButton.get_keyboard(bot.bot_id, custom_bot_user.user_language),
        )
    else:
        raise UnknownDeepLinkArgument(arg=deep_link_params)


@multi_bot_router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id

    bot = await bot_db.get_bot_by_token(message.bot.token)

    await _check_new_user(message, user_id)

    custom_bot_user = await custom_bot_user_db.get_custom_bot_user(bot.bot_id, message.from_user.id)

    try:
        options = await option_db.get_option(bot.options_id)
    except OptionNotFoundError:
        new_options_id = await create_bot_options()
        bot.options_id = new_options_id
        await bot_db.update_bot(bot)
        options = await option_db.get_option(new_options_id)
    start_msg = options.start_msg
    await message.answer(
        format_locales(start_msg[custom_bot_user.user_language.value], message.from_user, message.chat),
        reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(lang=custom_bot_user.user_language),
    )
    await state.set_state(CustomUserStates.MAIN_MENU)


@multi_bot_router.callback_query(lambda query: InlineSelectLanguageKb.callback_validator(query.data))
async def language_select_handler(query: CallbackQuery, state: FSMContext):
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
            await query.message.edit_reply_markup(
                reply_markup=InlineSelectLanguageKb.get_keyboard(
                    bot_id, bot_options.languages, custom_bot_user.user_language
                )
            )
