from enum import Enum

from pydantic import ConfigDict, Field, BaseModel

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.utils.keyboard_utils import make_webapp_info


class ReplyCustomBotMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SHOP = "🛍 Открыть магазин"
            PARTNER_SHIP = "🤝 Партнёрство"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="custom_bot_menu", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard(bot_id: int) -> ReplyKeyboardMarkup:
        actions = ReplyCustomBotMenuKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=actions.SHOP.value,
                        web_app=make_webapp_info(bot_id))
                ],
                [
                    KeyboardButton(
                        text=actions.PARTNER_SHIP.value,
                    )
                ]
            ], resize_keyboard=True, one_time_keyboard=False
        )
