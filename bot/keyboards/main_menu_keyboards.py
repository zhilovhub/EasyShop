from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from common_utils.keyboards.keyboard_utils import callback_json_validator, make_select_hex_web_app_info
from database.enums import UserLanguageValues, UserLanguageEmoji


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
            keyboard=[[KeyboardButton(text=actions.BACK_TO_BOT_MENU.value)]], resize_keyboard=True
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
                [KeyboardButton(text=actions.SETTINGS.value), KeyboardButton(text=actions.CONTACTS.value)],
                [
                    KeyboardButton(
                        text=actions.SHOP.value,
                    )
                ],
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
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
                [InlineKeyboardButton(text=actions.HEX_SELECT.value, web_app=make_select_hex_web_app_info())],
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
                        ),
                    ),
                    InlineKeyboardButton(
                        text="❌",
                        callback_data=InlineAcceptPublishProductKeyboard.callback_json(
                            actions.REJECT, bot_id, msg_id, product_id
                        ),
                    ),
                ]
            ]
        )


class InlineBackFromRefKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK = "backfromref"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot__backfromref", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlineBackFromRefKeyboard.Callback(a=action, bot_id=bot_id).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineBackFromRefKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(bot_id: int) -> InlineKeyboardMarkup:
        actions = InlineBackFromRefKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineBackFromRefKeyboard.callback_json(actions.BACK, bot_id),
                    ),
                ]
            ]
        )


class InlineSelectLanguageKb:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SELECT = "s"
            BACK = "back_fl"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="s_lang_sel", frozen=True)
        bot_id: int
        selected: UserLanguageValues | None
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, selected: UserLanguageValues | None, bot_id: int) -> str:
        return InlineSelectLanguageKb.Callback(a=action, selected=selected, bot_id=bot_id).model_dump_json(
            by_alias=True
        )

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineSelectLanguageKb.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(
        bot_id: int, languages: list[UserLanguageValues], selected_languages: list[UserLanguageValues]
    ) -> InlineKeyboardMarkup:
        def get_button_text(lang: UserLanguageValues) -> str:
            match lang:
                case UserLanguageValues.RUSSIAN:
                    return (
                        f"Русский {UserLanguageEmoji.RUSSIAN.value}"
                        f"{' ✅' if UserLanguageValues.RUSSIAN in selected_languages else ''}"
                    )
                case UserLanguageValues.ENGLISH:
                    return (
                        f"English {UserLanguageEmoji.ENGLISH.value}"
                        f"{' ✅' if UserLanguageValues.ENGLISH in selected_languages else ''}"
                    )
                case UserLanguageValues.HEBREW:
                    return (
                        f"עברית {UserLanguageEmoji.HEBREW.value}"
                        f"{' ✅' if UserLanguageValues.HEBREW in selected_languages else ''}"
                    )

        actions = InlineSelectLanguageKb.Callback.ActionEnum

        buttons = []
        for language in languages:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=get_button_text(language),
                        callback_data=InlineSelectLanguageKb.callback_json(
                            actions.SELECT, bot_id=bot_id, selected=language
                        ),
                    )
                ]
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlineSelectLanguageKb.callback_json(actions.BACK, bot_id=bot_id, selected=None),
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=buttons)
