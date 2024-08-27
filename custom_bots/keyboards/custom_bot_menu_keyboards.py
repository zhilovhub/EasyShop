from enum import Enum

from pydantic import ConfigDict, Field, BaseModel, ValidationError

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from common_utils.keyboards.keyboard_utils import callback_json_validator


from database.enums import UserLanguageEmoji, UserLanguageValues


class ReplyCustomBotMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SHOP = "🛍 Открыть магазин"
            SHOP_ENG = "🛍 Open Shop"
            SHOP_HEB = "🛍 חנות פתוחה"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="custom_bot_menu", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard(lang: UserLanguageValues) -> ReplyKeyboardMarkup:
        actions = ReplyCustomBotMenuKeyboard.Callback.ActionEnum

        match lang:
            case UserLanguageValues.RUSSIAN:
                text = actions.SHOP.value
            case UserLanguageValues.HEBREW:
                text = actions.SHOP_HEB.value
            case UserLanguageValues.ENGLISH | _:
                text = actions.SHOP_ENG.value

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=text,
                    )
                ],
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
        )


class InlineSelectLanguageKb:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SELECT = "s"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="c_lang_sel", frozen=True)
        bot_id: int
        selected: UserLanguageValues
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, selected: UserLanguageValues, bot_id: int) -> str:
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
        bot_id: int, languages: list[UserLanguageValues], current_lang: UserLanguageValues = UserLanguageValues.RUSSIAN
    ) -> InlineKeyboardMarkup:
        def get_button_text(lang: UserLanguageValues) -> str:
            match lang:
                case UserLanguageValues.RUSSIAN:
                    return (
                        f"Русский {UserLanguageEmoji.RUSSIAN.value}"
                        f"{' ✅' if current_lang == UserLanguageValues.RUSSIAN else ''}"
                    )
                case UserLanguageValues.ENGLISH:
                    return (
                        f"English {UserLanguageEmoji.ENGLISH.value}"
                        f"{' ✅' if current_lang == UserLanguageValues.ENGLISH else ''}"
                    )
                case UserLanguageValues.HEBREW:
                    return (
                        f"עברית {UserLanguageEmoji.HEBREW.value}"
                        f"{' ✅' if current_lang == UserLanguageValues.HEBREW else ''}"
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

        return InlineKeyboardMarkup(inline_keyboard=buttons)
