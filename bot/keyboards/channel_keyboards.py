from enum import Enum

from pydantic import ValidationError, Field, ConfigDict, BaseModel

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from bot.utils.keyboard_utils import get_bot_channels, get_bot_username, get_channel_contest, get_bot_channel_post
from bot.keyboards.keyboard_utils import callback_json_validator


class ReplyBackChannelMenuKeyboard:  # TODO should not be common for every channel's back
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK_TO_CHANNEL_MENU = "🔙 Назад"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="back_to_channel_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyBackChannelMenuKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=actions.BACK_TO_CHANNEL_MENU.value
                    )
                ]
            ], resize_keyboard=True
        )


class InlineChannelsListKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            OPEN_CHANNEL = "channel"
            BACK_TO_MAIN_MENU = "back_main_menu"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="cl", frozen=True)
        a: ActionEnum

        bot_id: int
        channel_id: int | None = Field(alias="ci")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            channel_id: int | None
    ) -> str:
        return InlineChannelsListKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            channel_id=channel_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineChannelsListKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(
            bot_id: int
    ) -> InlineKeyboardMarkup:
        actions = InlineChannelsListKeyboard.Callback.ActionEnum

        all_channels = await get_bot_channels(bot_id=bot_id)
        channels_buttons = [
            InlineKeyboardButton(
                text='@' + channel[1],
                callback_data=InlineChannelsListKeyboard.callback_json(
                    actions.OPEN_CHANNEL, bot_id=bot_id, channel_id=channel[0].channel_id
                )
            ) for channel in all_channels
        ]
        resized_channels_buttons = [channels_buttons[i:i + 4] for i in range(0, len(channels_buttons), 4)]

        return InlineKeyboardMarkup(inline_keyboard=[
            *resized_channels_buttons,
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlineChannelsListKeyboard.callback_json(
                        actions.BACK_TO_MAIN_MENU, bot_id, None
                    )
                ),
                InlineKeyboardButton(
                    text="📢 Добавить в канал",
                    url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel"
                )
            ],
        ])


class InlineChannelMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            EDIT_POST_MESSAGE = "epm"
            CREATE_POST_MESSAGE = "cpm"
            EDIT_CONTEST = "ec"
            CREATE_CONTEST = "cc"

            ANALYTICS = "an"
            LEAVE_CHANNEL = "lc"

            BACK_CHANNELS_LIST = "back_cc"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="cm", frozen=True)
        a: ActionEnum

        bot_id: int
        channel_id: int = Field(alias="ci")
        post_message_id: int | None = Field(alias="pmi", default=None)

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            channel_id: int,
            post_message_id: int | None = None
    ) -> str:
        to_exclude = set()
        if post_message_id is None:
            to_exclude.add("post_message_id")

        return InlineChannelMenuKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            channel_id=channel_id,
            post_message_id=post_message_id
        ).model_dump_json(by_alias=True, exclude=to_exclude)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineChannelMenuKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(
            bot_id: int,
            channel_id: int
    ) -> InlineKeyboardMarkup:
        actions = InlineChannelMenuKeyboard.Callback.ActionEnum

        channel_post = await get_bot_channel_post(bot_id=bot_id)
        if channel_post:
            channel_post_button = InlineKeyboardButton(
                text="Редактировать запись",
                callback_data=InlineChannelMenuKeyboard.callback_json(
                    actions.EDIT_POST_MESSAGE, bot_id, channel_id, channel_post.post_message_id
                )
            )
        else:
            channel_post_button = InlineKeyboardButton(
                text="Создать запись",
                callback_data=InlineChannelMenuKeyboard.callback_json(
                    actions.CREATE_POST_MESSAGE, bot_id, channel_id, channel_post.post_message_id
                )
            )

        channel_contest = await get_channel_contest(channel_id=channel_id)
        if channel_contest:
            contest_button = InlineKeyboardButton(
                text="Редактировать конкурс",
                callback_data=InlineChannelMenuKeyboard.callback_json(
                    actions.EDIT_CONTEST, bot_id, channel_id, channel_contest.contest_id
                )
            )
        else:
            contest_button = InlineKeyboardButton(
                text="🆕 Создать конкурс",
                callback_data=InlineChannelMenuKeyboard.callback_json(
                    actions.CREATE_CONTEST, bot_id, channel_id
                )
            )

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    contest_button
                ],
                [
                    channel_post_button,
                    InlineKeyboardButton(
                        text="Аналитика",
                        callback_data=InlineChannelMenuKeyboard.callback_json(
                            actions.ANALYTICS, bot_id, channel_id
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Права бота",
                        url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineChannelMenuKeyboard.callback_json(
                            actions.BACK_CHANNELS_LIST, bot_id, channel_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="🛑 Выйти из канала",
                        callback_data=InlineChannelMenuKeyboard.callback_json(
                            actions.LEAVE_CHANNEL, bot_id, channel_id
                        )
                    )
                ]
            ],
        )
