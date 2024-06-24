from bot.main import contest_user_db
from typing import Optional

from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from database.models.channel_post_model import ContestTypeValues
from bot.utils.keyboard_utils import *
from bot.utils import MessageTexts, make_admin_panel_webapp_info

from database.models.order_model import OrderStatusValues

free_trial_start_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Начать пробный период",
                             callback_data="start_trial")
    ]
])


def create_continue_subscription_kb(bot_id: Optional[int | None]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Продлить подписку",
                                 callback_data=f"continue_subscription_{bot_id}")
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
                text=("🔸 " if current_status ==
                              OrderStatusValues.WAITING_PAYMENT else "") + "Ждет оплаты",
                callback_data=f"order_waiting_payment:{order_id}:{msg_id}:{chat_id}"),
        ],
        [
            InlineKeyboardButton(text=("🔸 " if current_status == OrderStatusValues.PROCESSING else "") + "Выполнять",
                                 callback_data=f"order_process:{order_id}:{msg_id}:{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text="Отменить ❌", callback_data=f"order_pre_cancel:{order_id}:{msg_id}:{chat_id}"),
            InlineKeyboardButton(
                text="Завершить ✅", callback_data=f"order_finish:{order_id}:{msg_id}:{chat_id}")
        ]
    ])


def create_user_order_kb(order_id: str, msg_id: int = 0, chat_id: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Задать вопрос", callback_data=f"ask_question:{order_id}:{msg_id}:{chat_id}")
        ],
        [
            InlineKeyboardButton(
                text="Отменить заказ", callback_data=f"order_pre_cancel:{order_id}:{msg_id}:{chat_id}")
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
            InlineKeyboardButton(
                text="Точно отменить?", callback_data=f"order_cancel:{order_id}:{msg_id}:{chat_id}")
        ],
        [
            InlineKeyboardButton(
                text="Назад", callback_data=f"order_back_to_order:{order_id}:{msg_id}:{chat_id}")
        ]
    ])


def get_back_keyboard(back_text: str = MessageTexts.BACK_BUTTON_TEXT.value) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=back_text)]
    ], resize_keyboard=True)


def get_confirm_media_upload_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Готово"), KeyboardButton(text="Очистить")],
    ], resize_keyboard=True)


def get_stock_import_options_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    callback_data = f":{bot_id}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="import_menu:replace_all" + callback_data),
            InlineKeyboardButton(text="2", callback_data="import_menu:replace_duplicates" + callback_data),
            InlineKeyboardButton(text="3", callback_data="import_menu:dont_replace_duplicates" + callback_data),
        ]
    ])


async def get_competition_menu_keyboard(competition_id: int) -> InlineKeyboardMarkup:
    callback_metadata = str(competition_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Название (для Вас)", callback_data="competition_menu:name:" + callback_metadata)
            ],
            [
                InlineKeyboardButton(
                    text="Содержание", callback_data="competition_menu:description:" + callback_metadata),
                InlineKeyboardButton(
                    text="Медиафайлы", callback_data="competition_menu:media_files:" + callback_metadata),
            ],
            [
                InlineKeyboardButton(
                    text="Длительность", callback_data="competition_menu:" + callback_metadata),
                InlineKeyboardButton(
                    text="Условия", callback_data="competition_menu:" + callback_metadata),
            ],
            [
                # InlineKeyboardButton(text="Рандомайзер", callback_data="competition_menu:" + callback_metadata),
            ],
            [
                InlineKeyboardButton(
                    text="Кнопка", callback_data="competition_menu:" + callback_metadata),
            ],
            # [
            #     InlineKeyboardButton(text="Аналитика", callback_data="competition_menu:" + callback_metadata),
            # ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад", callback_data="competition_menu:back_to_competitions_list:" + callback_metadata),
                InlineKeyboardButton(
                    text="🔎 Предпросмотр", callback_data="competition_menu:demo:" + callback_metadata),
                InlineKeyboardButton(
                    text="⏭ Дальше", callback_data="competition_menu:" + callback_metadata),
            ]
        ],
    )


async def get_competitions_list_keyboard(bot_id: int, channel_id: int) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{channel_id}"
    competitions = await get_bot_competitions(channel_id, bot_id)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            *[
                [InlineKeyboardButton(
                    text=i.name,
                    callback_data=f"competitions_list:competition" + callback_metadata + f":{i.competition_id}")]
                for i in competitions
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад", callback_data="competitions_list:back_to_channel_menu" + callback_metadata)
            ]
        ],
    )


async def get_inline_channel_menu_keyboard(bot_id: int, channel_id: int) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{channel_id}"
    try:
        await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=False)
        channel_post_button = InlineKeyboardButton(
            text="Редактировать запись", callback_data="channel_menu:edit_post" + callback_metadata)
    except ChannelPostNotFound:
        channel_post_button = InlineKeyboardButton(
            text="Создать запись", callback_data="channel_menu:create_post" + callback_metadata)

    try:
        channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=True)
        contest_button = InlineKeyboardButton(
            text="Редактировать конкурс", callback_data="channel_menu:edit_post" + callback_metadata + f":{channel_post.channel_post_id}")
    except ChannelPostNotFound:
        contest_button = InlineKeyboardButton(
            text="🆕 Создать конкурс", callback_data="channel_menu:create_contest" + callback_metadata)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                # InlineKeyboardButton(
                #     text="🎲 Созданные конкурсы", callback_data="channel_menu:competitions_list" + callback_metadata),
                contest_button
            ],
            [
                channel_post_button,
                InlineKeyboardButton(
                    text="Аналитика", callback_data="channel_menu:analytics" + callback_metadata)
            ],
            [
                InlineKeyboardButton(
                    text="Права бота", callback_data="channel_menu:manage" + callback_metadata,
                    url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel")
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад", callback_data="channel_menu:back_to_channels_list" + callback_metadata),
                InlineKeyboardButton(
                    text="🛑 Выйти из канала", callback_data="channel_menu:leave_channel" + callback_metadata)
            ]
        ],
    )


async def get_inline_bot_channels_list_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}"

    all_channels = await get_bot_channels(bot_id=bot_id)

    channels_buttons = [
        InlineKeyboardButton(text='@' + channel[1],
                             callback_data=f"bot_menu:channel{callback_metadata}:{channel[0].channel_id}") for channel
        in all_channels
    ]
    resized_channels_buttons = [channels_buttons[i:i + 4]
                                for i in range(0, len(channels_buttons), 4)]

    return InlineKeyboardMarkup(inline_keyboard=[
        *resized_channels_buttons,
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="bot_menu:back_to_menu" + callback_metadata),
            InlineKeyboardButton(
                text="📢 Добавить в канал",
                callback_data="bot_menu:add_to_channel" + callback_metadata,
                url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel"
            )
        ],
    ])


async def get_custom_bot_ad_channels_list_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}"
    all_channels = await get_bot_channels(bot_id=bot_id)
    channels_buttons = [
        InlineKeyboardButton(text='@' + channel[1],
                             callback_data=f"ad_channel{callback_metadata}:{channel[0].channel_id}") for channel
        in all_channels
    ]
    resized_channels_buttons = [channels_buttons[i:i + 4]
                                for i in range(0, len(channels_buttons), 4)]

    return InlineKeyboardMarkup(inline_keyboard=[
        *resized_channels_buttons,
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="back_to_partnership" + callback_metadata),
            InlineKeyboardButton(
                text="➕ Добавить канал",
                url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel&admin=post_messages"
            )
        ],
    ])


async def get_inline_bot_mailing_menu_extra_settings_keyboard(bot_id: int,
                                                              mailing_id: int,
                                                              is_notification_sound: bool,
                                                              is_link_preview: bool) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{mailing_id}"
    notification_text = "Звуковое уведомление: "
    if is_notification_sound:
        notification_text += "вкл"
    else:
        notification_text += "выкл"
    preview_text = "Предпросмотр ссылок: "
    if is_link_preview:
        preview_text += "вкл"
    else:
        preview_text += "выкл"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=notification_text, callback_data="mailing_menu:toggle_notigication_sound" +
                                                      callback_metadata
            )
        ],
        [
            InlineKeyboardButton(
                text=preview_text, callback_data="mailing_menu:toggle_link_preview" + callback_metadata
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="bot_menu:mailing_menu" + callback_metadata
            ),
        ]
    ])


async def get_inline_bot_mailing_menu_accept_deleting_keyboard(bot_id: int, mailing_id: int) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{mailing_id}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Удалить", callback_data="mailing_menu:accept_delete" + callback_metadata
            ),
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="bot_menu:mailing_menu" + callback_metadata
            )
        ]
    ])


async def get_inline_bot_mailing_start_confirm_keybaord(bot_id: int, mailing_id: int) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{mailing_id}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Отправить", callback_data="mailing_menu:accept_start" + callback_metadata
            ),
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="bot_menu:mailing_menu" + callback_metadata
            )
        ]
    ])


async def get_inline_bot_mailing_menu_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    mailing = await get_bot_mailing(bot_id=bot_id)
    callback_metadata = f":{bot_id}:{mailing.mailing_id}"
    if mailing.is_delayed:
        delay_btn = InlineKeyboardButton(
            text="Убрать откладывание", callback_data="mailing_menu:cancel_delay" + callback_metadata)
    else:
        delay_btn = InlineKeyboardButton(
            text="Отложить", callback_data="mailing_menu:delay" + callback_metadata)
    if mailing.is_running == True:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="Статистика", callback_data="mailing_menu:check_mailing_stats" + callback_metadata)],
                [InlineKeyboardButton(
                    text="Отменить", callback_data="mailing_menu:stop_mailing" + callback_metadata)]
            ]
        )
    if mailing.has_button:
        inline_buttons = [
            [
                InlineKeyboardButton(
                    text="Ссылка кнопки", callback_data="mailing_menu:button_url" + callback_metadata
                ),
                InlineKeyboardButton(
                    text="Текст на кнопке", callback_data="mailing_menu:button_text" + callback_metadata
                )
            ],
            [
                InlineKeyboardButton(
                    text="Удалить кнопку", callback_data="mailing_menu:delete_button" + callback_metadata
                )
            ]
        ]
    else:
        inline_buttons = [
            [
                InlineKeyboardButton(
                    text="Добавить кнопку", callback_data="mailing_menu:add_button" + callback_metadata
                ),
            ]
        ]

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Текст сообщения", callback_data="mailing_menu:message" + callback_metadata
            ),
            InlineKeyboardButton(
                text="Медиафайлы", callback_data="mailing_menu:media" + callback_metadata
            )
        ],
        *inline_buttons,
        [
            InlineKeyboardButton(
                text="Запустить", callback_data="mailing_menu:start" + callback_metadata
            ),
            InlineKeyboardButton(
                text="Проверить", callback_data="mailing_menu:demo" + callback_metadata
            ),
        ],
        [
            delay_btn,
            InlineKeyboardButton(
                text="Доп настройки", callback_data="mailing_menu:extra_settings" + callback_metadata
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="bot_menu:back_to_menu" + callback_metadata),
            InlineKeyboardButton(
                text="Удалить рассылку", callback_data="mailing_menu:delete_mailing" + callback_metadata
            ),
        ]
    ])


CUSTOM_BOT_KEYBOARD_BUTTONS = {
    "open_shop": "🛍 Открыть магазин",
    "partnership": "🤝 Партнёрство",
}


def get_custom_bot_menu_keyboard(button_text: str | None, bot_id: int) -> ReplyKeyboardMarkup:
    if not button_text:
        button_text = CUSTOM_BOT_KEYBOARD_BUTTONS['open_shop']
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=CUSTOM_BOT_KEYBOARD_BUTTONS['open_shop'],
                        web_app=make_webapp_info(bot_id))],
        [
            KeyboardButton(text=CUSTOM_BOT_KEYBOARD_BUTTONS['partnership'])
        ]
    ], resize_keyboard=True, one_time_keyboard=False)


def get_partnership_inline_kb(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Заказать рекламу", callback_data=f"request_ad:{bot_id}")
        ],
        [
            InlineKeyboardButton(text="Принять рекламное предложение", callback_data=f"accept_ad:{bot_id}")
        ],
    ])


def get_request_ad_keyboard(bot_id: int, admin_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Связаться с админом", url=f"t.me/{admin_username}")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=f"back_to_partnership:{bot_id}")
        ]
    ])


async def get_accept_ad_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить канал",
                                 url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel&admin=post_messages")
        ],
        [
            InlineKeyboardButton(text="Продолжить", callback_data=f"continue_ad_accept:{bot_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_partnership:{bot_id}")
        ]
    ])


def get_show_inline_button(bot_id: int, partnership: bool = False) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Открыть магазин", web_app=make_webapp_info(bot_id))]
    ], resize_keyboard=True, one_time_keyboard=False)


def get_inline_delete_button(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Удалить", callback_data=f"product:delete_{product_id}")]
    ])


async def get_inline_bot_channel_post_menu_keyboard(bot_id: int, channel_id: int, is_contest: bool = False) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{channel_id}"
    channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=is_contest)
    if is_contest:
        callback_metadata += f":{channel_post.channel_post_id}"

    if channel_post.is_delayed:
        delay_btn = InlineKeyboardButton(
            text="Убрать откладывание", callback_data="channel_menu:cancel_delay" + callback_metadata)
    else:
        delay_btn = InlineKeyboardButton(
            text="Отложить", callback_data="channel_menu:delay" + callback_metadata)
    if channel_post.is_running == True:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="Отменить", callback_data="channel_menu:stop_post" + callback_metadata)]
            ]
        )
    inline_buttons = [
        [
            # InlineKeyboardButton(
            #     text="Длительность конкурса", callback_data="channel_menu:get_contest_end_date" + callback_metadata
            # ),
            InlineKeyboardButton(
                text="Условия выполнения", callback_data="channel_menu:pick_contest_type" + callback_metadata
            )
        ],
        # [
        #     InlineKeyboardButton(
        #         text="Кол-во победителей", callback_data="channel_menu:get_contest_winner_amount" + callback_metadata),
        #     InlineKeyboardButton(
        #         text="Текст кнопки участия", callback_data="channel_menu:get_contest_button_text" + callback_metadata)
        # ]
    ]
    # if channel_post.contest_type == ContestTypeValues.SPONSOR:
    #     inline_buttons.append(
    #         [
    #             InlineKeyboardButton(
    #                 text="Выбрать спонсоров", callback_data="channel_menu:get_sponsors" + callback_metadata
    #             )
    #         ]
    #     )
    if channel_post.is_contest is False:
        if channel_post.has_button:
            inline_buttons = [
                [
                    InlineKeyboardButton(
                        text="Ссылка кнопки", callback_data="channel_menu:button_url" + callback_metadata
                    ),
                    InlineKeyboardButton(
                        text="Текст на кнопке", callback_data="channel_menu:button_text" + callback_metadata
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Удалить кнопку", callback_data="channel_menu:delete_button" + callback_metadata
                    )
                ]
            ]
        else:
            inline_buttons = [
                [
                    InlineKeyboardButton(
                        text="Добавить кнопку", callback_data="channel_menu:add_button" + callback_metadata
                    ),
                ]
            ]

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Текст сообщения", callback_data="channel_menu:message" + callback_metadata
            ),
            InlineKeyboardButton(
                text="Медиафайлы", callback_data="channel_menu:media" + callback_metadata
            )
        ],
        *inline_buttons,
        [
            InlineKeyboardButton(
                text="Отправить", callback_data="channel_menu:start" + callback_metadata
            ),
            InlineKeyboardButton(
                text="Проверить", callback_data="channel_menu:demo" + callback_metadata
            ),
        ],
        [
            delay_btn,
            InlineKeyboardButton(
                text="Доп настройки", callback_data="channel_menu:extra_settings" + callback_metadata
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="channel_menu:back_to_channel_list" + callback_metadata),
            InlineKeyboardButton(
                text="Удалить пост", callback_data="channel_menu:delete_channel_post" + callback_metadata
            ),
        ]
    ])


async def get_inline_bot_channel_post_start_confirm_keybaord(bot_id: int, channel_id: int, is_contest: bool = False) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{channel_id}"
    if is_contest:
        channel_post = await channel_post_db.get_channel_post(channel_id, True)
        callback_metadata += f":{channel_post.channel_post_id}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Отправить", callback_data="channel_menu:accept_start" + callback_metadata
            ),
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="channel_menu:back_to_channel_list" + callback_metadata
            )
        ]
    ])


async def get_inline_bot_channel_post_menu_extra_settings_keyboard(bot_id: int,
                                                                   channel_id: int,
                                                                   is_notification_sound: bool,
                                                                   is_link_preview: bool,
                                                                   is_contest: bool = False) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{channel_id}"
    if is_contest:
        channel_post = await channel_post_db.get_channel_post(channel_id, True)
        callback_metadata += f":{channel_post.channel_post_id}"
    notification_text = "Звуковое уведомление: "
    if is_notification_sound:
        notification_text += "вкл"
    else:
        notification_text += "выкл"
    preview_text = "Предпросмотр ссылок: "
    if is_link_preview:
        preview_text += "вкл"
    else:
        preview_text += "выкл"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=notification_text, callback_data="channel_menu:toggle_notigication_sound" +
                                                      callback_metadata
            )
        ],
        [
            InlineKeyboardButton(
                text=preview_text, callback_data="channel_menu:toggle_link_preview" + callback_metadata
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="channel_menu:back_to_editing_channel_post" + callback_metadata
            ),
        ]
    ])


async def get_inline_bot_channel_post_menu_accept_deleting_keyboard(bot_id: int, channel_id: int, is_contest: bool = False) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{channel_id}"
    if is_contest:
        channel_post = await channel_post_db.get_channel_post(channel_id, True)
        callback_metadata += f":{channel_post.channel_post_id}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Удалить", callback_data="channel_menu:accept_delete" + callback_metadata
            ),
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="channel_menu:back_to_editing_channel_post" + callback_metadata
            )
        ]
    ])


async def get_contest_menu_keyboard(bot_id: int, channel_id: int, is_contest: bool = True) -> InlineKeyboardMarkup:
    callback_metadata = f":{bot_id}:{channel_id}"
    if is_contest:
        channel_post = await channel_post_db.get_channel_post(channel_id, True)
        callback_metadata += f":{channel_post.channel_post_id}"
    keyboard = [
        [
            InlineKeyboardButton(
                text="Рандомайзер", callback_data="channel_menu:pick_random_contest" + callback_metadata
            ),
            InlineKeyboardButton(
                text="Спонсорство", callback_data="channel_menu:pick_sponsor_contest" + callback_metadata
            )
        ],
        [
            InlineKeyboardButton(
                text="Длительность конкурса", callback_data="channel_menu:get_contest_end_date" + callback_metadata
            ),
        ],
        [
            InlineKeyboardButton(
                text="Кол-во победителей", callback_data="channel_menu:get_contest_winner_amount" + callback_metadata),
            InlineKeyboardButton(
                text="Текст кнопки участия", callback_data="channel_menu:get_contest_button_text" + callback_metadata)
        ],
    ]
    if channel_post.contest_type == ContestTypeValues.SPONSOR:
        keyboard.append([
            InlineKeyboardButton(
                text="Выбрать спонсоров", callback_data="channel_menu:get_sponsors" + callback_metadata
            )
        ])
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Назад", callback_data="channel_menu:back_to_editing_channel_post" + callback_metadata
        )
    ],)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_contest_inline_join_button(channel_id: int):
    try:
        channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=True)
        users = await contest_user_db.get_contest_users_by_contest_id(channel_post.channel_post_id)
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{channel_post.button_text.split()[0]} ({len(users)})", callback_data=f"{channel_post.button_query}"
                    ),
                ],
            ]
        )
    except ChannelPostNotFound:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Конкурс закончен", callback_data=f"{channel_post.button_query}"
                    ),
                ],
            ]
        )
