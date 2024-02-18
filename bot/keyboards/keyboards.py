from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from bot.locales import DefaultLocale


def create_change_order_status_kb(order_id: str, is_processing: bool, msg_id: int = 0, chat_id: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ожидание" if is_processing else "Ожидание 🔸" , callback_data=f"order_backlog:{order_id}:{msg_id}:{chat_id}"),
            InlineKeyboardButton(text="Выполнять 🔸" if is_processing else "Выполнять", callback_data=f"order_process:{order_id}:{msg_id}:{chat_id}")
        ],
        [
            InlineKeyboardButton(text="Отменить ❌", callback_data=f"order_pre_cancel:{order_id}:{msg_id}:{chat_id}"),
            InlineKeyboardButton(text="Завершить ✅", callback_data=f"order_finish:{order_id}:{msg_id}:{chat_id}")
        ]
    ])


def create_cancel_order_kb(order_id: str, msg_id: int = 0, chat_id: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Отменить заказ", callback_data=f"order_pre_cancel:{order_id}:{msg_id}:{chat_id}")
        ]
    ])


def create_cancel_confirm_kb(order_id: str, msg_id: int = 0, chat_id: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Точно отменить?", callback_data=f"order_cancel:{order_id}:{msg_id}:{chat_id}")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=f"order_back_to_order:{order_id}:{msg_id}:{chat_id}")
        ]
    ])


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
