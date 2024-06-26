from enum import Enum

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pydantic import ValidationError, Field, ConfigDict, BaseModel

from bot.keyboards.keyboard_utils import callback_json_validator
from bot.utils.keyboard_utils import get_bot_mailing


class InlinePostMessageMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            REMOVE_DELAY = "remove_delay"
            DELAY = "delay"

            BUTTON_ADD = "button_add"
            BUTTON_URL = "button_url"
            BUTTON_TEXT = "button_text"
            BUTTON_DELETE = "button_delete"

            POST_MESSAGE_TEXT = "message"
            POST_MESSAGE_MEDIA = "media"

            START = "start"
            DEMO = "demo"

            EXTRA_SETTINGS = "extra_settings"

            BACK_TO_MAIN_MENU = "back_main_menu"
            DELETE_POST_MESSAGE = "delete"

            # RUNNING ACTIONS
            STATISTICS = "statistics"
            CANCEL = "cancel"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="post_message", frozen=True)
        a: ActionEnum

        bot_id: int
        mailing_id: int = Field(alias="mi")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            mailing_id: int,
    ) -> str:
        return InlinePostMessageMenuKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            mailing_id=mailing_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlinePostMessageMenuKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(
            bot_id: int
    ) -> InlineKeyboardMarkup:
        actions = InlinePostMessageMenuKeyboard.Callback.ActionEnum

        mailing = await get_bot_mailing(bot_id=bot_id)
        mailing_id = mailing.mailing_id

        if mailing.is_delayed:
            delay_btn = InlineKeyboardButton(
                text="Убрать откладывание",
                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                    actions.REMOVE_DELAY, bot_id, mailing_id
                )
            )
        else:
            delay_btn = InlineKeyboardButton(
                text="Отложить",
                callback_data=InlinePostMessageMenuKeyboard.callback_json(
                    actions.DELAY, bot_id, mailing_id
                )
            )

        if mailing.is_running is True:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Статистика",
                            callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                actions.STATISTICS, bot_id, mailing_id
                            )
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Отменить",
                            callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                actions.CANCEL, bot_id, mailing_id
                            )
                        )
                    ]
                ]
            )
        else:
            if mailing.has_button:
                button_buttons = [
                    [
                        InlineKeyboardButton(
                            text="Ссылка кнопки",
                            callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                actions.BUTTON_URL, bot_id, mailing_id
                            )
                        ),
                        InlineKeyboardButton(
                            text="Текст на кнопке",
                            callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                actions.BUTTON_TEXT, bot_id, mailing_id
                            )
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Удалить кнопку",
                            callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                actions.BUTTON_DELETE, bot_id, mailing_id
                            )
                        )
                    ]
                ]
            else:
                button_buttons = [
                    [
                        InlineKeyboardButton(
                            text="Добавить кнопку",
                            callback_data=InlinePostMessageMenuKeyboard.callback_json(
                                actions.BUTTON_ADD, bot_id, mailing_id
                            )
                        ),
                    ]
                ]

            return InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Текст сообщения",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.POST_MESSAGE_TEXT, bot_id, mailing_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="Медиафайлы",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.POST_MESSAGE_MEDIA, bot_id, mailing_id
                        )
                    )
                ],
                *button_buttons,
                [
                    InlineKeyboardButton(
                        text="Запустить",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.START, bot_id, mailing_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="Проверить",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.DEMO, bot_id, mailing_id
                        )
                    ),
                ],
                [
                    delay_btn,
                    InlineKeyboardButton(
                        text="Доп настройки",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.EXTRA_SETTINGS, bot_id, mailing_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.BACK_TO_MAIN_MENU, bot_id, mailing_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="Удалить рассылку",
                        callback_data=InlinePostMessageMenuKeyboard.callback_json(
                            actions.DELETE_POST_MESSAGE, bot_id, mailing_id
                        )
                    ),
                ]
            ])
