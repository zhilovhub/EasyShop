from enum import Enum

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from pydantic import ValidationError, ConfigDict, Field, BaseModel

from bot.keyboards.keyboard_utils import callback_json_validator


class ReplyBackQuestionMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK_TO_MAIN_MENU = "🔙 Назад"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="question_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyBackQuestionMenuKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=actions.BACK_TO_MAIN_MENU.value
                    )
                ]
            ], resize_keyboard=True
        )


class InlineOrderQuestionKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            APPROVE = "aa"
            CANCEL = "ca"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="oq", frozen=True)
        a: ActionEnum

        order_id: str = Field(alias="o")
        msg_id: int = Field(default=0, alias="m")
        chat_id: int = Field(default=0, alias="c")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            order_id: str,
            msg_id: int,
            chat_id: int
    ) -> str:
        return InlineOrderQuestionKeyboard.Callback(
            a=action,
            order_id=order_id,
            msg_id=msg_id,
            chat_id=chat_id,
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineOrderQuestionKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(
            order_id: str,
            msg_id: int = 0,
            chat_id: int = 0
    ) -> InlineKeyboardMarkup:
        actions = InlineOrderQuestionKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅",
                    callback_data=InlineOrderQuestionKeyboard.callback_json(
                        actions.APPROVE, order_id, msg_id, chat_id
                    )
                ),
                InlineKeyboardButton(
                    text="❌",
                    callback_data=InlineOrderQuestionKeyboard.callback_json(
                        actions.CANCEL, order_id, msg_id, chat_id
                    )
                )
            ],
        ])
