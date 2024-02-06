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

router = Router(name="users")
router.message.filter(ChatTypeFilter(chat_type='private'))


@router.message(CommandStart())
async def start_cmd(message: Message):
    await message.reply("Hello")
