from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from bot.locales import DefaultLocale


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


def get_inline_delete_button(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удалить", callback_data=f"product:delete_{product_id}")]
    ])
