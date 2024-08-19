from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from common_utils.keyboards.keyboard_utils import callback_json_validator


class MainStartKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            ABOUT_PRODUCT = "product_info"
            START_REF = "ref_start"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="mainn_kb", frozen=True)
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum) -> str:
        return MainStartKeyboard.Callback(a=action).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            MainStartKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        actions = MainStartKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔎 Инструкция", url="https://ezshoptg.tilda.ws/"),
                    InlineKeyboardButton(
                        text="ℹ️ О продукте",
                        callback_data=MainStartKeyboard.callback_json(actions.ABOUT_PRODUCT),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🤝 Реферальная система", callback_data=MainStartKeyboard.callback_json(actions.START_REF)
                    )
                ],
                [InlineKeyboardButton(text="🔮 Подписаться на канал", url="t.me/EzShopOfficial")],
                [
                    InlineKeyboardButton(text="🔐 Получить токен", url="t.me/BotFather"),
                ],
            ],
        )
