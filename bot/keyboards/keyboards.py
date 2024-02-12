from aiogram import Bot
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from bot.locales import DefaultLocale
from bot.utils.database import DbBot


def get_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=DefaultLocale.back_button())]
    ], resize_keyboard=True)


def get_bot_menu_keyboard(web_app_info: WebAppInfo) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text="Стартовое сообщение"),
            KeyboardButton(text="Сообщение затычка")
        ],
        [
            KeyboardButton(text="Магазин", web_app=web_app_info),
            KeyboardButton(text="Список товаров")
        ],
        [
            KeyboardButton(text="Добавить товар")
        ],
        [
            KeyboardButton(text="Запустить бота"),
            KeyboardButton(text="Остановить бота")
        ],
        [
            KeyboardButton(text="Удалить бота")
        ]
    ], resize_keyboard=True, one_time_keyboard=False)


def create_main_menu_keyboard():
    buttons = DefaultLocale.main_menu_buttons()
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons['add'], callback_data="main:create_bot")
        ],
        [
            InlineKeyboardButton(text=buttons['bots'], callback_data="main:my_bots")
        ],
        [
            InlineKeyboardButton(text=buttons['profile'], callback_data="main:profile")
        ],
    ])


async def create_my_bots_keyboard(bots: list[DbBot]):
    buttons = []
    for bot in bots:
        found_bot = Bot(bot.token)
        found_bot_data = await found_bot.get_me()
        buttons.append([InlineKeyboardButton(text=found_bot_data.full_name, callback_data=f"select_bot:{bot.token}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons + [
        [
            InlineKeyboardButton(text=DefaultLocale.back_to_menu_button(), callback_data="main:back_to_menu")
        ],
    ])


def create_selected_bot_keyboard(token: str):
    locales = DefaultLocale.selected_bot_buttons()
    return InlineKeyboardMarkup(inline_keyboard=
        [
            [
                InlineKeyboardButton(text=locales[option],
                                     callback_data=f"bot:{option}:{token}")
            ] for option in locales] +
        [
            [
                InlineKeyboardButton(text=DefaultLocale.back_to_menu_button(),
                                     callback_data="main:back_to_menu")
            ],
        ])
