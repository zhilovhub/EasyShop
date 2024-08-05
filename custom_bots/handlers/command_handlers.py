from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, CommandObject

from common_utils.bot_utils import create_bot_options
from custom_bots.multibot import CustomUserStates
from custom_bots.utils.utils import format_locales
from custom_bots.handlers.routers import multi_bot_router

from common_utils.keyboards.keyboards import InlineCustomBotModeProductKeyboardButton
from common_utils.exceptions.bot_exceptions import UnknownDeepLinkArgument
from common_utils.broadcasting.broadcasting import send_event, EventTypes
from custom_bots.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard, InlineShopCustomBotKeyboard

from database.config import custom_bot_user_db, bot_db, option_db
from database.models.bot_model import BotNotFoundError
from database.models.option_model import OptionNotFoundError
from database.models.custom_bot_user_model import CustomBotUserNotFoundError

from logs.config import custom_bot_logger, extra_params


async def _check_new_user(message: Message, user_id: int):
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
        custom_bot_logger.info(
            f"user_id={user_id}: user called /start at bot_id={bot.bot_id}",
            extra=extra_params(user_id=user_id, bot_id=bot.bot_id)
        )

        try:
            await custom_bot_user_db.get_custom_bot_user(bot.bot_id, user_id)
        except CustomBotUserNotFoundError:
            custom_bot_logger.info(
                f"user_id={user_id}: user not found in database, trying to add to it",
                extra=extra_params(user_id=user_id, bot_id=bot.bot_id)
            )
            await custom_bot_user_db.add_custom_bot_user(bot.bot_id, user_id)
            if user_id == bot.created_by:
                await send_event(message.from_user, EventTypes.FIRST_ADMIN_MESSAGE, event_bot=message.bot)
            else:
                await send_event(message.from_user, EventTypes.FIRST_USER_MESSAGE, event_bot=message.bot)
    except BotNotFoundError as e:
        custom_bot_logger.warning("Бот не инициализирован", exc_info=e)
        await Bot(message.bot.token).delete_webhook()
        return await message.answer("Бот не инициализирован")


@multi_bot_router.message(CommandStart(deep_link=True))
async def deep_link_start_handler(message: Message, state: FSMContext, command: CommandObject):
    """
    :raises UnknownDeepLinkArgument:
    """
    deep_link_params = command.args.split()

    bot = await bot_db.get_bot_by_token(message.bot.token)
    # Проверяем, новый ли пользователь
    await _check_new_user(message, message.from_user.id)

    if deep_link_params[0].startswith("product_"):
        product_id = int(deep_link_params[0].strip().split('_')[-1])
        await state.set_state(CustomUserStates.MAIN_MENU)
        return await message.answer(
            "<b>Страничка товара:</b>",
            reply_markup=InlineCustomBotModeProductKeyboardButton.get_keyboard(product_id, bot.bot_id)
        )
    elif deep_link_params[0] == "web_app":
        await state.set_state(CustomUserStates.MAIN_MENU)
        return await message.answer(
            "<b>Наш магазин:</b>",
            reply_markup=InlineShopCustomBotKeyboard.get_keyboard(bot.bot_id)
        )
    else:
        raise UnknownDeepLinkArgument(arg=deep_link_params)


@multi_bot_router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id

    bot = await bot_db.get_bot_by_token(message.bot.token)

    await _check_new_user(message, user_id)

    try:
        options = await option_db.get_option(bot.options_id)
    except OptionNotFoundError:
        new_options_id = await create_bot_options()
        bot.options_id = new_options_id
        await bot_db.update_bot(bot)
        options = await option_db.get_option(new_options_id)
    start_msg = options.start_msg
    await message.answer(
        format_locales(start_msg, message.from_user, message.chat),
        reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(
            bot.bot_id
        )
    )
    await state.set_state(CustomUserStates.MAIN_MENU)
