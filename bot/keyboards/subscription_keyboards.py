from enum import Enum
from typing import Optional

from pydantic import ValidationError, ConfigDict, Field, BaseModel

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from common_utils.keyboards.keyboard_utils import callback_json_validator


class InlineSubscriptionContinueKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CONTINUE_SUBSCRIPTION = "continue_subscription"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="subscription", frozen=True)
        a: ActionEnum

        bot_id: Optional[int | None]

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int | None) -> str:
        return InlineSubscriptionContinueKeyboard.Callback(a=action, bot_id=bot_id).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineSubscriptionContinueKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(bot_id: int | None) -> InlineKeyboardMarkup:
        actions = InlineSubscriptionContinueKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Продлить подписку",
                        callback_data=InlineSubscriptionContinueKeyboard.callback_json(
                            actions.CONTINUE_SUBSCRIPTION, bot_id
                        ),
                    ),
                ],
                [
                    InlineKeyboardButton(text="Реферальная система", callback_data="ref_on_start"),
                ],
            ],
        )


class InlineAdminRefundKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            REFUND_SUBSCRIPTION = "refund"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="refund", frozen=True)
        a: ActionEnum

        bot_id: int | None
        payment_id: int = 0  # TODO

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int | None, payment_id: int) -> str:
        return InlineAdminRefundKeyboard.Callback(a=action, bot_id=bot_id, payment_id=payment_id).model_dump_json(
            by_alias=True
        )

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineAdminRefundKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(bot_id: int | None, payment_id: int) -> InlineKeyboardMarkup:
        actions = InlineAdminRefundKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="↩️ Сделать возврат",
                        callback_data=InlineAdminRefundKeyboard.callback_json(
                            actions.REFUND_SUBSCRIPTION, bot_id, payment_id
                        ),
                    ),
                ],
            ],
        )
