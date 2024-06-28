from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from bot.main import contest_user_db
from bot.utils.keyboard_utils import *


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


def get_show_inline_button(bot_id: int, partnership: bool = False) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Открыть магазин", web_app=make_webapp_info(bot_id))]
    ], resize_keyboard=True, one_time_keyboard=False)


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
    if not channel_post.is_contest:
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
