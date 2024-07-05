from enum import Enum

from pydantic import ValidationError, Field, ConfigDict, BaseModel

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from bot.utils.keyboard_utils import get_bot_post_message
from bot.enums.post_message_type import PostMessageType
from bot.keyboards.keyboard_utils import callback_json_validator


class UnknownPostMessageType(Exception):
    pass


class ReplyConfirmMediaFilesKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CONFIRM = "✅ Готово"
            CLEAR = "🧹 Очистить"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="confirm_media_files", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyConfirmMediaFilesKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=actions.CONFIRM.value
                    ),
                    KeyboardButton(
                        text=actions.CLEAR.value
                    )
                ]
            ], resize_keyboard=True
        )


class ReplyBackPostMessageMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK_TO_POST_MESSAGE_MENU = "🔙 Назад"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="back_to_post_message_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=actions.BACK_TO_POST_MESSAGE_MENU.value
                    )
                ]
            ], resize_keyboard=True
        )


class InlinePostMessageAcceptDeletingKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            ACCEPT_DELETE = "a"
            BACK_TO_POST_MESSAGE_MENU = "b"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="p", frozen=True)
        a: ActionEnum

        bot_id: int = Field(alias="b")
        channel_id: int | None = Field(default=None, alias="c")
        post_message_id: int = Field(alias="mi")
        post_message_type: PostMessageType = Field(alias="t")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            post_message_id: int,
            post_message_type: PostMessageType,
            channel_id: int | None = None
    ) -> str:
        to_exclude = set()
        if channel_id is None:
            to_exclude.add("channel_id")

        return InlinePostMessageAcceptDeletingKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            post_message_id=post_message_id,
            post_message_type=post_message_type,
            channel_id=channel_id
        ).model_dump_json(by_alias=True, exclude=to_exclude)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlinePostMessageAcceptDeletingKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(
            bot_id: int,
            post_message_id: int,
            post_message_type: PostMessageType,
            channel_id: int | None
    ) -> InlineKeyboardMarkup:
        actions = InlinePostMessageAcceptDeletingKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=InlinePostMessageAcceptDeletingKeyboard.callback_json(
                        actions.ACCEPT_DELETE, bot_id, post_message_id, post_message_type, channel_id
                    )
                ),
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlinePostMessageAcceptDeletingKeyboard.callback_json(
                        actions.BACK_TO_POST_MESSAGE_MENU, bot_id, post_message_id, post_message_type, channel_id
                    )
                )
            ]
        ])


class InlinePostMessageMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            REMOVE_DELAY = "r"
            DELAY = "dy"

            BUTTON_ADD = "ba"
            BUTTON_URL = "bu"
            BUTTON_TEXT = "bt"
            BUTTON_DELETE = "bd"

            POST_MESSAGE_TEXT = "m"
            POST_MESSAGE_MEDIA = "me"

            START = "s"
            DEMO = "d"

            EXTRA_SETTINGS = "es"

            BACK = "bk"
            DELETE_POST_MESSAGE = "de"

            # RUNNING ACTIONS
            STATISTICS = "st"
            CANCEL = "ca"

            # CONTEST_ACTIONS
            WINNERS_COUNT = "wc"
            CONTEST_FINISH_DATE = "fd"

            # RUNNING CONTEST
            PRE_FINISH = "pf"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="pm", frozen=True)
        a: ActionEnum

        bot_id: int = Field(alias="b")
        channel_id: int | None = Field(default=None, alias="c")
        post_message_id: int = Field(alias="m")
        post_message_type: PostMessageType = Field(alias="t")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            post_message_id: int,
            post_message_type: PostMessageType,
            channel_id: int | None = None
    ) -> str:
        to_exclude = set()
        if channel_id is None:
            to_exclude.add("channel_id")

        return InlinePostMessageMenuKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            post_message_id=post_message_id,
            post_message_type=post_message_type,
            channel_id=channel_id
        ).model_dump_json(by_alias=True, exclude=to_exclude)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlinePostMessageMenuKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(
            bot_id: int,
            post_message_type: PostMessageType,
            channel_id: int | None
    ) -> InlineKeyboardMarkup:
        actions = InlinePostMessageMenuKeyboard.Callback.ActionEnum

        post_message = await get_bot_post_message(bot_id, post_message_type)
        post_message_id = post_message.post_message_id

        match post_message_type:
            case PostMessageType.MAILING:
                delete_button_text = "🗑 Удалить рассылку"
            case PostMessageType.CHANNEL_POST:
                delete_button_text = "🗑 Удалить запись"
            case PostMessageType.CONTEST:
                delete_button_text = "🗑 Удалить конкурс"
            case _:
                raise UnknownPostMessageType

        if post_message.is_delayed:
            delay_btn = InlineKeyboardButton(
                text="Убрать откладывание",
                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                    actions.REMOVE_DELAY, bot_id, post_message_id, post_message_type, channel_id
                )
            )
        else:
            delay_btn = InlineKeyboardButton(
                text="Отложить",
                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                    actions.DELAY, bot_id, post_message_id, post_message_type, channel_id
                )
            )

        if post_message.is_running:
            if post_message_type != PostMessageType.CONTEST:
                return InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Статистика",
                                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                    actions.STATISTICS, bot_id, post_message_id, post_message_type
                                )
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="Отменить",
                                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                    actions.CANCEL, bot_id, post_message_id, post_message_type, channel_id
                                )
                            )
                        ]
                    ]
                )
            else:
                return InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Досрочно завершить",
                                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                    actions.PRE_FINISH, bot_id, post_message_id, post_message_type, channel_id
                                )
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="Отменить",
                                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                    actions.CANCEL, bot_id, post_message_id, post_message_type, channel_id
                                )
                            )
                        ]
                    ]
                )
        else:
            if post_message.has_button:
                button_buttons = [
                    [
                        InlineKeyboardButton(
                            text="Ссылка кнопки",
                            callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                actions.BUTTON_URL, bot_id, post_message_id, post_message_type, channel_id
                            )
                        ),
                        InlineKeyboardButton(
                            text="Текст на кнопке",
                            callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                actions.BUTTON_TEXT, bot_id, post_message_id, post_message_type, channel_id
                            )
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Удалить кнопку",
                            callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                actions.BUTTON_DELETE, bot_id, post_message_id, post_message_type, channel_id
                            )
                        )
                    ]
                ]
            else:
                if post_message.post_message_type != PostMessageType.CONTEST:
                    button_buttons = [
                        [
                            InlineKeyboardButton(
                                text="Добавить кнопку",
                                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                    actions.BUTTON_ADD, bot_id, post_message_id, post_message_type, channel_id
                                )
                            ),
                        ]
                    ]
                else:
                    button_buttons = [
                        [
                            InlineKeyboardButton(
                                text="Количество победителей",
                                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                    actions.WINNERS_COUNT, bot_id, post_message_id, post_message_type, channel_id
                                )
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="Дата окончания конкурса",
                                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                    actions.CONTEST_FINISH_DATE, bot_id, post_message_id, post_message_type, channel_id
                                )
                            )
                        ]
                    ]
            buttons = [
                [
                    InlineKeyboardButton(
                        text="Текст сообщения",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.POST_MESSAGE_TEXT, bot_id, post_message_id, post_message_type, channel_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="Медиафайлы",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.POST_MESSAGE_MEDIA, bot_id, post_message_id, post_message_type, channel_id
                        )
                    )
                ],
            ]
            if button_buttons:
                buttons = buttons + button_buttons
            buttons = buttons + [[
                    InlineKeyboardButton(
                        text="Запустить",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.START, bot_id, post_message_id, post_message_type, channel_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="Проверить",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.DEMO, bot_id, post_message_id, post_message_type, channel_id
                        )
                    ),
                ],
                [
                    delay_btn,
                    InlineKeyboardButton(
                        text="Доп настройки",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.EXTRA_SETTINGS, bot_id, post_message_id, post_message_type, channel_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.BACK, bot_id, post_message_id, post_message_type, channel_id
                        )
                    ),
                    InlineKeyboardButton(
                        text=delete_button_text,
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.DELETE_POST_MESSAGE, bot_id, post_message_id, post_message_type, channel_id
                        )
                    ),
                ]]

            return InlineKeyboardMarkup(inline_keyboard=buttons)


class InlinePostMessageExtraSettingsKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            NOTIFICATION_SOUND = "ns"
            LINK_PREVIEW = "lp"

            BACK_TO_POST_MESSAGE_MENU = "db"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="e", frozen=True)
        a: ActionEnum

        bot_id: int = Field(alias="b")
        channel_id: int | None = Field(default=None, alias="c")
        post_message_id: int = Field(alias="mi")
        post_message_type: PostMessageType = Field(alias="t")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            post_message_id: int,
            post_message_type: PostMessageType,
            channel_id: int | None = None
    ) -> str:
        to_exclude = set()
        if channel_id is None:
            to_exclude.add("channel_id")

        return InlinePostMessageExtraSettingsKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            post_message_id=post_message_id,
            post_message_type=post_message_type,
            channel_id=channel_id
        ).model_dump_json(by_alias=True, exclude=to_exclude)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlinePostMessageExtraSettingsKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(
            bot_id: int,
            post_message_id: int,
            is_notification_sound: bool,
            is_link_preview: bool,
            post_message_type: PostMessageType,
            channel_id: int
    ) -> InlineKeyboardMarkup:
        actions = InlinePostMessageExtraSettingsKeyboard.Callback.ActionEnum

        notification_text = "Звуковое уведомление: "

        if is_notification_sound:
            notification_text += "✅"
        else:
            notification_text += "❌"

        preview_text = "Предпросмотр ссылок: "
        if is_link_preview:
            preview_text += "✅"
        else:
            preview_text += "❌"

        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=notification_text,
                    callback_data=InlinePostMessageExtraSettingsKeyboard.callback_json(
                        actions.NOTIFICATION_SOUND, bot_id, post_message_id, post_message_type, channel_id
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text=preview_text,
                    callback_data=InlinePostMessageExtraSettingsKeyboard.callback_json(
                        actions.LINK_PREVIEW, bot_id, post_message_id, post_message_type, channel_id
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlinePostMessageExtraSettingsKeyboard.callback_json(
                        actions.BACK_TO_POST_MESSAGE_MENU, bot_id, post_message_id, post_message_type, channel_id
                    )
                ),
            ]
        ])


class InlinePostMessageStartConfirmKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            START_CONFIRM = "s"

            BACK_TO_POST_MESSAGE_MENU = "b"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="es", frozen=True)
        a: ActionEnum

        bot_id: int = Field(alias="b")
        channel_id: int | None = Field(default=None, alias="c")
        post_message_id: int = Field(alias="mi")
        post_message_type: PostMessageType = Field(alias="t")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            post_message_id: int,
            post_message_type: PostMessageType,
            channel_id: int | None = None
    ) -> str:
        to_exclude = set()
        if channel_id is None:
            to_exclude.add("channel_id")

        return InlinePostMessageStartConfirmKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            post_message_id=post_message_id,
            post_message_type=post_message_type,
            channel_id=channel_id
        ).model_dump_json(by_alias=True, exclude=to_exclude)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlinePostMessageStartConfirmKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(
            bot_id: int,
            post_message_id: int,
            post_message_type: PostMessageType,
            channel_id: int
    ) -> InlineKeyboardMarkup:
        actions = InlinePostMessageStartConfirmKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отправить",
                    callback_data=InlinePostMessageStartConfirmKeyboard.callback_json(
                        actions.START_CONFIRM, bot_id, post_message_id, post_message_type, channel_id
                    )
                ),
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlinePostMessageStartConfirmKeyboard.callback_json(
                        actions.BACK_TO_POST_MESSAGE_MENU, bot_id, post_message_id, post_message_type, channel_id
                    )
                )
            ]
        ])
