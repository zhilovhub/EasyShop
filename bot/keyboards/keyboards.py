from enum import Enum
from typing import Optional

from aiogram.types import WebAppInfo
from bot.config import WEB_APP_URL, WEB_APP_PORT

from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from bot.utils import make_webapp_info, MessageTexts, make_admin_panel_webapp_info

from database.models.order_model import OrderStatusValues

free_trial_start_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Начать пробный период", callback_data="start_trial")
    ]
])


def create_continue_subscription_kb(bot_id: Optional[int | None]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Продлить подписку", callback_data=f"continue_subscription_{bot_id}")
        ]
    ])


def create_change_order_status_kb(order_id: str, msg_id: int = 0, chat_id: int = 0,
                                  current_status: OrderStatusValues = OrderStatusValues.BACKLOG) \
        -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=("🔸 " if current_status == OrderStatusValues.BACKLOG else "") + "Ожидание",
                                 callback_data=f"order_backlog:{order_id}:{msg_id}:{chat_id}"),
            InlineKeyboardButton(
                text=("🔸 " if current_status == OrderStatusValues.WAITING_PAYMENT else "") + "Ждет оплаты",
                callback_data=f"order_waiting_payment:{order_id}:{msg_id}:{chat_id}"),
        ],
        [
            InlineKeyboardButton(text=("🔸 " if current_status == OrderStatusValues.PROCESSING else "") + "Выполнять",
                                 callback_data=f"order_process:{order_id}:{msg_id}:{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="Отменить ❌", callback_data=f"order_pre_cancel:{order_id}:{msg_id}:{chat_id}"),
            InlineKeyboardButton(text="Завершить ✅", callback_data=f"order_finish:{order_id}:{msg_id}:{chat_id}")
        ]
    ])


def create_user_order_kb(order_id: str, msg_id: int = 0, chat_id: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Задать вопрос", callback_data=f"ask_question:{order_id}:{msg_id}:{chat_id}")
        ],
        [
            InlineKeyboardButton(text="Отменить заказ", callback_data=f"order_pre_cancel:{order_id}:{msg_id}:{chat_id}")
        ]
    ])


def create_confirm_question_kb(order_id: str, msg_id: int, chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅",
                                 callback_data=f"approve_ask_question:{order_id}:{msg_id}:{chat_id}"),
            InlineKeyboardButton(text="❌",
                                 callback_data=f"cancel_ask_question")
        ],
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
        [KeyboardButton(text=MessageTexts.BACK_BUTTON_TEXT.value)]
    ], resize_keyboard=True)


class ReplyBotMenuButtons(Enum):
    SETTINGS = "⚙ Настройки бота"
    CONTACTS = "☎ Контакты"
    SHOP = "🛍 Мой магазин"
    ADMIN_APP = "Страница админа"


def get_reply_bot_menu_keyboard(bot_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ReplyBotMenuButtons.SETTINGS.value),
                KeyboardButton(text=ReplyBotMenuButtons.CONTACTS.value)
            ],
            [
                KeyboardButton(text=ReplyBotMenuButtons.SHOP.value, web_app=make_webapp_info(bot_id=bot_id))
            ],
            [
                KeyboardButton(text=ReplyBotMenuButtons.ADMIN_APP.value, web_app=WebAppInfo(url=f"{WEB_APP_URL}:822"))
            ]
        ],
        resize_keyboard=True
    )


def get_inline_bot_goods_menu_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧮 Количество товаров", callback_data="bot_menu:goods_count"),
                InlineKeyboardButton(text="📋 Страница настройки товаров", web_app=make_admin_panel_webapp_info(bot_id))
            ],
            [
                InlineKeyboardButton(text="🆕 Добавить товар", callback_data="bot_menu:add_new_good"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="bot_menu:back_from_goods"),
            ],
        ],
    )


def get_inline_bot_menu_keyboard(bot_status: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👋 Приветственный текст", callback_data="bot_menu:start_text"),
                InlineKeyboardButton(text="🗣 Текст объяснения", callback_data="bot_menu:explain_text")
            ],
            [
                InlineKeyboardButton(text="⛔ Остановить бота", callback_data="bot_menu:stop_bot")
                if bot_status == "online" else InlineKeyboardButton(
                    text="🚀 Запустить бота", callback_data="bot_menu:start_bot"),
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="bot_menu:statistic"),
                InlineKeyboardButton(text="📦 Мои товары", callback_data="bot_menu:goods")
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить бота", callback_data="bot_menu:delete_bot")
            ]
        ],
    )


def get_custom_bot_menu_keyboard(button_text: str, bot_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Открыть магазин", web_app=make_webapp_info(bot_id))]
    ], resize_keyboard=True, one_time_keyboard=False)


def get_inline_delete_button(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удалить", callback_data=f"product:delete_{product_id}")]
    ])
