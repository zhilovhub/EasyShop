import datetime
from bot.exceptions.exceptions import *
from bot.locales.misc import format_locales
from bot.main import bot, db, dp
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, Chat, User
from aiogram import Bot, Dispatcher, Router, types
from aiogram.utils.markdown import hbold, hitalic
from bot import config
from bot.config import logger
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F
from typing import *
from bot.filters.chat_type import ChatTypeFilter
from bot.utils.database import DbUser
from bot.keyboards import users as kb

router = Router(name="users")
router.message.filter(ChatTypeFilter(chat_type='private'))


@router.message(Command(commands=['cancel', 'c'], prefix='/!'))
async def cancel_cmd(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.reply('Нет действия для отмены.')
        return None
    await message.reply(f'Действие отменено.')
    await state.clear()


@router.message(CommandStart())
async def start_cmd(message: Message):
    try:
        user = await db.get_user(message.from_user.id)
    except UserNotFound:
        logger.info(f"user {message.from_user.id} not found in db, creating new instance...")
        if message.from_user.language_code in config.LOCALES:
            locale = message.from_user.language_code
        else:
            locale = "default"
        await db.add_user(DbUser(
            user_id=message.from_user.id, registered_at=datetime.datetime.now(), status="new", locale=locale)
        )
        user = await db.get_user(message.from_user.id)
    await message.answer(format_locales(text=config.LOCALES[user.locale].start_message, user=message.from_user,
                                        chat=message.chat), reply_markup=kb.lang_select_keyboard)
