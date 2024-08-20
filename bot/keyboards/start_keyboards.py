from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from common_utils.keyboards.keyboard_utils import callback_json_validator


class ShortDescriptionKeyboard:  # Краткий рассказ о продукте
    class Callback(BaseModel):
        class ActionEnum(Enum):
            START_USING = "su"
            REF_DESCRIPTION = "rd"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="shkb", frozen=True)
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum) -> str:
        return ShortDescriptionKeyboard.Callback(a=action).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            ShortDescriptionKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        actions = ShortDescriptionKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Начать пользоваться",
                        callback_data=ShortDescriptionKeyboard.callback_json(actions.START_USING),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🤝 Реферальная система",
                        callback_data=ShortDescriptionKeyboard.callback_json(actions.REF_DESCRIPTION),
                    ),
                ],
                [
                    InlineKeyboardButton(text="🔮 Подписаться на канал", url="t.me/EzShopOfficial"),
                ],
            ],
        )


class InstructionKeyboard:  # Инструкции
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK = "back_instr"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="ikb", frozen=True)
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum) -> str:
        return InstructionKeyboard.Callback(a=action).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InstructionKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        actions = InstructionKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔐 Получить токен", url="t.me/BotFather"),
                    InlineKeyboardButton(text="🔎 Инструкция", url="https://ezshoptg.tilda.ws/"),
                ],
                [
                    InlineKeyboardButton(text="🌐 Меню", callback_data=InstructionKeyboard.callback_json(actions.BACK)),
                ],
            ],
        )


class RefShortDescriptionKeyboard:  # Краткий рассказ о продукте для рефералов
    class Callback(BaseModel):
        class ActionEnum(Enum):
            REWARDS = "rs"
            BACK = "back__short"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="rdkb", frozen=True)
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum) -> str:
        return RefShortDescriptionKeyboard.Callback(a=action).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            RefShortDescriptionKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        actions = RefShortDescriptionKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🏆 Награды", callback_data=RefShortDescriptionKeyboard.callback_json(actions.REWARDS)
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🌐 Меню", callback_data=RefShortDescriptionKeyboard.callback_json(actions.BACK)
                    ),
                ],
            ],
        )


class RefFullDescriptionKeyboard:  # Полный рассказ о продукте для рефералов
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CONTINUE = "co"
            BACK = "back__full"
            MENU = "menu"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="rfdk", frozen=True)
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum) -> str:
        return RefFullDescriptionKeyboard.Callback(a=action).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            RefFullDescriptionKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        actions = RefFullDescriptionKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⏭ Продолжить", callback_data=RefFullDescriptionKeyboard.callback_json(actions.CONTINUE)
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data=RefFullDescriptionKeyboard.callback_json(actions.BACK)
                    ),
                    InlineKeyboardButton(
                        text="🌐 Меню", callback_data=RefFullDescriptionKeyboard.callback_json(actions.MENU)
                    ),
                ],
            ],
        )


class RefLinkKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK = "back"
            MENU = "menu"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="rlk", frozen=True)
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum) -> str:
        return RefLinkKeyboard.Callback(a=action).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            RefLinkKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        actions = RefLinkKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔙 Назад", callback_data=RefLinkKeyboard.callback_json(actions.BACK)),
                    InlineKeyboardButton(text="🌐 Меню", callback_data=RefLinkKeyboard.callback_json(actions.MENU)),
                ],
            ],
        )
