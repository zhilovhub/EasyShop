from enum import Enum

from pydantic import ValidationError, ConfigDict, Field, BaseModel

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from common_utils.keyboards.utils import get_product_by_id
from common_utils.keyboards.keyboard_utils import callback_json_validator

from database.models.order_model import OrderItem

from logs.config import custom_bot_logger


class ReplyGetReviewMarkKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            ONE = "1️⃣"
            TWO = "2️⃣"
            THREE = "3️⃣"
            FOUR = "4️⃣"
            FIVE = "5️⃣"
            BACK = "Назад 🔙"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="grm", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyGetReviewMarkKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=actions.ONE.value),
                    KeyboardButton(text=actions.TWO.value),
                    KeyboardButton(text=actions.THREE.value),
                    KeyboardButton(text=actions.FOUR.value),
                    KeyboardButton(text=actions.FIVE.value),
                ],
                [
                    KeyboardButton(text=actions.BACK.value),
                ],
            ], resize_keyboard=True, one_time_keyboard=False
        )


class ReplyReviewBackKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK = "Назад 🔙"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="rb", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyReviewBackKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=actions.BACK.value),
                ],
            ], resize_keyboard=True, one_time_keyboard=False
        )


class InlinePickReviewProductKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            PICK_PRODUCT = "prp"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="prpkb", frozen=True)
        a: ActionEnum

        product_id: int = Field(alias="prid")

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, product_id: int) -> str:
        return InlinePickReviewProductKeyboard.Callback(
            a=action, product_id=product_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlinePickReviewProductKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(order_json: dict[int, OrderItem]) -> InlineKeyboardMarkup:
        actions = InlinePickReviewProductKeyboard.Callback.ActionEnum
        product_buttons = []
        for product_id in list(order_json.keys()):
            product = await get_product_by_id(product_id)
            custom_bot_logger.info(f"product {product}")
            product_buttons.append(
                [InlineKeyboardButton(
                    text=f"{product.name}",
                    callback_data=InlinePickReviewProductKeyboard.callback_json(actions.PICK_PRODUCT, product_id))]
            )
        return InlineKeyboardMarkup(
            inline_keyboard=product_buttons
        )
