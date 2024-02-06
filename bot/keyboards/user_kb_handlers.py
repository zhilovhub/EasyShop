from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot import config
from bot.main import bot, db
from bot.utils.database import DbUser
from bot.locales.misc import format_locales
from aiogram import Bot, Dispatcher, Router, types


router = Router(name="users_callback")


@router.callback_query(lambda q: q.data.startswith('lang:'))
async def start_query_handler(query: CallbackQuery, state: FSMContext):
    lang = query.data.split(':')[-1]
    if lang not in config.LOCALES:
        lang = "default"
    user = await db.get_user(query.from_user.id)
    user.locale = lang
    await db.update_user(user)
    await query.answer(format_locales(config.LOCALES[lang].locale_set, query.from_user, query.message.chat))
    await query.message.edit_reply_markup(None)
