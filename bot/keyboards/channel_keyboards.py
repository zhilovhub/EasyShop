from enum import Enum

from pydantic import ValidationError, Field, ConfigDict, BaseModel

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from bot.keyboards.keyboard_utils import callback_json_validator
from bot.utils.keyboard_utils import get_bot_channels, get_bot_username


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
