from enum import Enum
from typing import Optional

from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from bot.utils.keyboard_utils import *
from bot.utils import MessageTexts, make_admin_panel_webapp_info

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


def get_back_keyboard(back_text: str = MessageTexts.BACK_BUTTON_TEXT.value) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=back_text)]
    ], resize_keyboard=True)


class ReplyBotMenuButtons(Enum):
    SETTINGS = "⚙ Настройки бота"
    CONTACTS = "☎ Контакты"
    SHOP = "🛍 Мой магазин"


def get_reply_bot_menu_keyboard(bot_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ReplyBotMenuButtons.SETTINGS.value),
                KeyboardButton(text=ReplyBotMenuButtons.CONTACTS.value)
            ],
            [
                KeyboardButton(text=ReplyBotMenuButtons.SHOP.value, web_app=make_webapp_info(bot_id=bot_id))
            ]
        ],
        resize_keyboard=True
    )


def get_inline_bot_goods_menu_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧮 Количество товаров", callback_data="bot_menu:goods_count"),
                InlineKeyboardButton(text="📋 Список товаров", web_app=make_admin_panel_webapp_info(bot_id))
            ],
            [
                InlineKeyboardButton(text="🆕 Добавить товар", callback_data="bot_menu:add_new_good"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="bot_menu:back_to_menu"),
            ],
        ],
    )


async def get_competition_menu_keyboard(competition_id: int) -> InlineKeyboardMarkup:
    callback_metadata = str(competition_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Название (для Вас)", callback_data="competition_menu:name:" + callback_metadata)
            ],
            [
                InlineKeyboardButton(text="Содержание", callback_data="competition_menu:description:" + callback_metadata),
                InlineKeyboardButton(text="Медиафайлы", callback_data="competition_menu:media_files:" + callback_metadata),
            ],
            [
                InlineKeyboardButton(text="Длительность", callback_data="competition_menu:" + callback_metadata),
                InlineKeyboardButton(text="Условия", callback_data="competition_menu:" + callback_metadata),
            ],
            [
                # InlineKeyboardButton(text="Рандомайзер", callback_data="competition_menu:" + callback_metadata),
            ],
            [
                InlineKeyboardButton(text="Кнопка", callback_data="competition_menu:" + callback_metadata),
            ],
            # [
            #     InlineKeyboardButton(text="Аналитика", callback_data="competition_menu:" + callback_metadata),
            # ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="competition_menu:back_to_competitions_list:" + callback_metadata),
                InlineKeyboardButton(text="🔎 Предпросмотр", callback_data="competition_menu:demo:" + callback_metadata),
                InlineKeyboardButton(text="⏭ Дальше", callback_data="competition_menu:" + callback_metadata),
            ]
        ],
    )


async def get_competitions_list_keyboard(bot_id: int, channel_id: int) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{channel_id}"
    competitions = await get_bot_competitions(channel_id, bot_id)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            *[
                [InlineKeyboardButton(text=i.name, callback_data=f"competitions_list:competition" + callback_metadata + f":{i.competition_id}")]
                for i in competitions
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="competitions_list:back_to_channel_menu" + callback_metadata)
            ]
        ],
    )


async def get_inline_channel_menu_keyboard(bot_id: int, channel_id: int) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{channel_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎲 Созданные конкурсы", callback_data="channel_menu:competitions_list" + callback_metadata),
                InlineKeyboardButton(text="🆕 Создать конкурс", callback_data="channel_menu:create_competition" + callback_metadata)
            ],
            [
                InlineKeyboardButton(text="🛑 Выйти из канала", callback_data="channel_menu:leave_channel" + callback_metadata)
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="channel_menu:back_to_channels_list" + callback_metadata)
            ]
        ],
    )


async def get_inline_bot_channels_list_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    all_channels = await get_bot_channels(bot_id=bot_id)

    channels_buttons = [
        InlineKeyboardButton(text='@' + channel[1], callback_data=f"bot_menu:channel:{channel[0].channel_id}") for channel in all_channels
    ]
    resized_channels_buttons = [channels_buttons[i:i + 4] for i in range(0, len(channels_buttons), 4)]

    return InlineKeyboardMarkup(inline_keyboard=[
        *resized_channels_buttons,
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="bot_menu:back_to_menu"),
            InlineKeyboardButton(
                text="📢 Добавить в канал",
                callback_data="bot_menu:add_to_channel",
                url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel"
            )
        ],
    ])


async def get_inline_bot_mailings_menu_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    channels_buttons = [
        InlineKeyboardButton(text='@' + channel[1], callback_data=f"bot_menu:channel:{channel[0].channel_id}") for channel in all_channels
    ]
    resized_channels_buttons = [channels_buttons[i:i + 4] for i in range(0, len(channels_buttons), 4)]

    return InlineKeyboardMarkup(inline_keyboard=[
        *resized_channels_buttons,
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="bot_menu:back_to_menu"),
            InlineKeyboardButton(
                text="📢 Добавить в канал",
                callback_data="bot_menu:add_to_channel",
                url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel"
            )
        ],
    ])


async def get_inline_bot_menu_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}"

    # channel_inline_button = InlineKeyboardButton(
    #                 text="📢 Добавить в канал",
    #                 callback_data="bot_menu:add_to_channel",
    #                 url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel"
    #     ) if not await get_bot_channels(bot_id=bot_id) else \
    #     InlineKeyboardButton(
    #         text="📢 Каналы бота",
    #         callback_data="bot_menu:channels"
    #     )


    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👋 Приветственный текст", callback_data="bot_menu:start_text" + callback_metadata),
                InlineKeyboardButton(text="🗣 Текст объяснения", callback_data="bot_menu:explain_text" + callback_metadata)
            ],
            [
                InlineKeyboardButton(text="⛔ Остановить бота", callback_data="bot_menu:stop_bot" + callback_metadata)
                if await get_bot_status(bot_id) == "online" else InlineKeyboardButton(
                    text="🚀 Запустить бота", callback_data="bot_menu:start_bot" + callback_metadata),
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="bot_menu:statistic" + callback_metadata),
                InlineKeyboardButton(text="📦 Мои товары", callback_data="bot_menu:goods" + callback_metadata)
            ],
            # [
            #     channel_inline_button
            # ],
            [
                InlineKeyboardButton(text="💌 Рассылки в ЛС", callback_data="bot_menu:mailings" + callback_metadata),
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить бота", callback_data="bot_menu:delete_bot" + callback_metadata)
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
