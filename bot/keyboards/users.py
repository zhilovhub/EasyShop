from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, CallbackData
from bot.config import LOCALES


lang_select_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
    ],
])


def create_main_menu_keyboard(lang):
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


def create_back_to_main_menu_keyboard(lang):
    locale = LOCALES[lang].back_to_menu_button
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=locale, callback_data="main:back_to_menu")
        ],
    ])
