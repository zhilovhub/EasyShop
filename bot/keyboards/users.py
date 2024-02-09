from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, CallbackData
from bot.config import LOCALES
from bot.utils.database import DbBot
from aiogram import Bot


lang_select_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
    ],
])


def create_main_menu_keyboard(lang: str):
    locales = LOCALES[lang].main_menu_buttons
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=locales['add'], callback_data="main:create_bot")
        ],
        [
            InlineKeyboardButton(text=locales['bots'], callback_data="main:my_bots")
        ],
        [
            InlineKeyboardButton(text=locales['profile'], callback_data="main:profile")
        ],
    ])


def create_back_to_main_menu_keyboard(lang: str):
    locale = LOCALES[lang].back_to_menu_button
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=locale, callback_data="main:back_to_menu")
        ],
    ])


async def create_my_bots_keyboard(lang: str, bots: list[DbBot]):
    locale_back = LOCALES[lang].back_to_menu_button
    buttons = []
    for bot in bots:
        found_bot = Bot(bot.token)
        found_bot_data = await found_bot.get_me()
        buttons.append([InlineKeyboardButton(text=found_bot_data.full_name, callback_data=f"select_bot:{bot.token}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons + [
        [
            InlineKeyboardButton(text=locale_back, callback_data="main:back_to_menu")
        ],
    ])


def create_selected_bot_keyboard(lang: str, token: str):
    locale_back = LOCALES[lang].back_to_menu_button
    locales = LOCALES[lang].selected_bot_buttons
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=locales[option], callback_data=f"bot:{option}:{token}")
        ] for option in locales] +
    [
        [
            InlineKeyboardButton(text=locale_back, callback_data="main:back_to_menu")
        ],
    ])

