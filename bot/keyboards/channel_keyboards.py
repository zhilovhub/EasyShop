from enum import Enum

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from pydantic import BaseModel, ConfigDict, Field


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