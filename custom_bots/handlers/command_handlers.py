from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard

from custom_bots.multibot import bot_db, custom_bot_user_db, CustomUserStates, format_locales
from custom_bots.handlers.routers import multi_bot_router
from custom_bots.utils.custom_bot_options import get_option

from database.models.bot_model import BotNotFound
from database.models.custom_bot_user_model import CustomBotUserNotFound

from logs.config import custom_bot_logger, extra_params


@multi_bot_router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
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
        await Bot(message.bot.token).delete_webhook()
        return await message.answer("Бот не инициализирован")

    await message.answer(
        format_locales(start_msg, message.from_user, message.chat),
        reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(
            bot.bot_id
        )
    )
    await state.set_state(CustomUserStates.MAIN_MENU)
