from enum import Enum

from pydantic import ConfigDict, Field, BaseModel

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from common_utils.keyboards.keyboard_utils import make_webapp_info


class ReplyCustomBotMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SHOP = "🛍 Открыть магазин"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="custom_bot_menu", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyCustomBotMenuKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=actions.SHOP.value,
                    )
                ],
            ], resize_keyboard=True, one_time_keyboard=False
        )


class InlineShopCustomBotKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SHOP = "🛍 Открыть магазин"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="custom_bot_web_app", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard(bot_id: int) -> InlineKeyboardMarkup:
        actions = InlineShopCustomBotKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=actions.SHOP.value,
                        web_app=make_webapp_info(bot_id)
                    )
                ],
            ]
        )
