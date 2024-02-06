import datetime

from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot import config
from bot.main import bot, db
from bot.utils.database import DbUser
from bot.locales.misc import format_locales
from aiogram import Router, Bot, Dispatcher
from bot.filters.chat_type import ChatTypeFilter
from bot.keyboards import users as kb
from bot.states import states
from re import fullmatch
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.types import MenuButtonWebApp, WebAppInfo
from bot.config import logger
from bot.utils.database import DbBot


router = Router(name="users_states")
router.message.filter(ChatTypeFilter(chat_type='private'))


@router.message(states.InputToken.input)
async def input_token_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.locale
    token = message.text
    if fullmatch(r"\d{10}:\w{35}", token):
        try:
            found_bot = Bot(token)
            found_bot_data = await found_bot.get_me()
            bot_fullname, bot_username = found_bot_data.full_name, found_bot_data.username
            await state.clear()
            await found_bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text=config.LOCALES[lang].open_web_app_button,
                                             web_app=WebAppInfo(url=config.WEB_APP_URL))
            )
            await message.answer(
                config.LOCALES[lang].bot_will_initialize.format(bot_fullname, bot_username),
                reply_markup=kb.create_back_to_main_menu_keyboard(lang)
            )
            new_bot = DbBot(bot_token=token, status="new", created_at=datetime.datetime.now(),
                            created_by=message.from_user.id, settings={}, locale=lang)
            await db.add_bot(new_bot)
        except TelegramUnauthorizedError:
            await message.answer(config.LOCALES[lang].bot_with_token_not_found)
        except Exception:
            logger.error(f"Error while adding new bot wit token {token} from user {message.from_user.id}", exc_info=True)
            await message.answer("Unknown error while adding bot")
    else:
        await message.answer(config.LOCALES[lang].incorrect_bot_token)
