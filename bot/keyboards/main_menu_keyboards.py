from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from common_utils.keyboards.keyboard_utils import callback_json_validator, make_select_hex_web_app_info


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
            SETTINGS = "⚙ Меню бота"
            CONTACTS = "☎ Контакты"
            SHOP = "🛍 Мой магазин"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="main_bot_menu", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
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
                    )
                ]
            ],
            resize_keyboard=True, one_time_keyboard=False
        )


class SelectHexColorWebAppInlineKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            HEX_SELECT = "🎨 Выбрать цвет"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="select_hex_web_app", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        actions = SelectHexColorWebAppInlineKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=actions.HEX_SELECT.value,
                        web_app=make_select_hex_web_app_info()
                    )
                ],
            ]
        )


class InlineAcceptPublishProductKeyboard:
    class Callback(BaseModel):

        class ActionEnum(Enum):
            ACCEPT = "accpt"
            REJECT = "rjct"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="ppa", frozen=True)
        a: ActionEnum

        bot_id: int
        msg_id: int
        pid: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int, msg_id: int, product_id: int) -> str:
        return InlineAcceptPublishProductKeyboard.Callback(
            a=action, bot_id=bot_id, msg_id=msg_id, pid=product_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineAcceptPublishProductKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(bot_id: int, msg_id: int, product_id) -> InlineKeyboardMarkup:
        actions = InlineAcceptPublishProductKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅",
                        callback_data=InlineAcceptPublishProductKeyboard.callback_json(
                            actions.ACCEPT, bot_id, msg_id, product_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="❌",
                        callback_data=InlineAcceptPublishProductKeyboard.callback_json(
                            actions.REJECT, bot_id, msg_id, product_id
                        )
                    )
                ]
            ]
        )
