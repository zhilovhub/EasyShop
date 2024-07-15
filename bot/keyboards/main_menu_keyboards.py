from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from common_utils.keyboards.keyboard_utils import make_webapp_info


class ReplyBackBotMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK_TO_BOT_MENU = "🔙 Назад"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="back_to_main_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyBackBotMenuKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=actions.BACK_TO_BOT_MENU.value
                    )
                ]
            ], resize_keyboard=True
        )


class ReplyBotMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SETTINGS = "⚙ Настройки бота"
            CONTACTS = "☎ Контакты"
            SHOP = "🛍 Мой магазин"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot_menu", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard(bot_id: int) -> ReplyKeyboardMarkup:
        actions = ReplyBotMenuKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=actions.SETTINGS.value),
                    KeyboardButton(text=actions.CONTACTS.value)
                ],
                [
                    KeyboardButton(
                        text=actions.SHOP.value,
                        web_app=make_webapp_info(bot_id=bot_id)
                    )
                ]
            ],
            resize_keyboard=True, one_time_keyboard=False
        )
