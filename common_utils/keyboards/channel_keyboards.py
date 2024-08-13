from enum import Enum

from pydantic import ValidationError, Field, ConfigDict, BaseModel

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from common_utils.keyboards.keyboard_utils import callback_json_validator


class InlineJoinContestKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            JOIN_CONTEST = "join"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="cj", frozen=True)
        a: ActionEnum

        bot_id: int
        post_message_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(
        action: Callback.ActionEnum,
        bot_id: int,
        post_message_id: int,
    ) -> str:
        return InlineJoinContestKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            post_message_id=post_message_id,
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineJoinContestKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(
        bot_id: int,
        contest_members_count: int,
        post_message_id: int,
    ) -> InlineKeyboardMarkup:
        actions = InlineJoinContestKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"Участвовать ({contest_members_count})",
                        callback_data=InlineJoinContestKeyboard.callback_json(
                            actions.JOIN_CONTEST,
                            bot_id,
                            post_message_id,
                        ),
                    )
                ]
            ]
        )
