from enum import Enum

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from bot.keyboards.keyboard_utils import callback_json_validator


class ExampleKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            EXAMPLE = "example_action"
            EXAMPLE2 = "example_action2"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="example", frozen=True)  # write callback_name into default
        a: ActionEnum

        some_args: str
        # bot_id: int
        # some_extra_parameter: str

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, some_arg: str) -> str:  # add more arguments here if you need
        return ExampleKeyboard.Callback(
            a=action, some_arg=some_arg
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            ExampleKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(some_arg: str) -> InlineKeyboardMarkup:
        actions = ExampleKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Some text",
                        callback_data=ExampleKeyboard.callback_json(
                            actions.EXAMPLE, some_arg
                        )
                    )
                ]
            ],
        )
