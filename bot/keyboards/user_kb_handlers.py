from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot import config
from bot.main import bot, db
from bot.utils.database import DbUser
from bot.locales.misc import format_locales
from aiogram import Bot, Dispatcher, Router, types
from . import users as kb
from bot.states import states


router = Router(name="users_callback")


@router.callback_query(lambda q: q.data.startswith('lang:'))
async def lang_query_handler(query: CallbackQuery, state: FSMContext):
    lang = query.data.split(':')[-1]
    if lang not in config.LOCALES:
        lang = "default"
    user = await db.get_user(query.from_user.id)
    user.locale = lang
    await db.update_user(user)
    await query.answer(format_locales(config.LOCALES[lang].locale_set, query.from_user, query.message.chat))
    await query.message.edit_reply_markup(None)
    await query.message.answer(format_locales(config.LOCALES[lang].about_message, query.from_user, query.message.chat),
                               reply_markup=kb.create_main_menu_keyboard(lang))


@router.callback_query(lambda q: q.data == "main:create_bot")
async def create_bot_query_handler(query: CallbackQuery, state: FSMContext):
    user = await db.get_user(query.from_user.id)
    lang = user.locale
    await state.set_state(states.InputToken.input)
    await query.message.edit_text(format_locales(config.LOCALES[lang].input_token, query.from_user, query.message.chat),
                                  reply_markup=kb.create_back_to_main_menu_keyboard(lang))
    pass


@router.callback_query(lambda q: q.data == "main:my_bots")
async def my_bots_query_handler(query: CallbackQuery, state: FSMContext):
    # TODO
    await query.answer("In dev")
    pass


@router.callback_query(lambda q: q.data == "main:profile")
async def profile_query_handler(query: CallbackQuery, state: FSMContext):
    # TODO
    await query.answer("In dev")
    pass


@router.callback_query(lambda q: q.data == "main:back_to_menu")
async def back_to_menu_query_handler(query: CallbackQuery, state: FSMContext):
    user = await db.get_user(query.from_user.id)
    lang = user.locale
    await state.clear()
    await query.message.edit_reply_markup(None)
    await query.message.edit_text(format_locales(config.LOCALES[lang].about_message, query.from_user, query.message.chat),
                                  reply_markup=kb.create_main_menu_keyboard(lang))
