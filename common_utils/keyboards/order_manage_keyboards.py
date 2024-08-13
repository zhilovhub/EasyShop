from enum import Enum

from pydantic import ValidationError, ConfigDict, Field, BaseModel

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from common_utils.keyboards.keyboard_utils import callback_json_validator

from database.models.order_model import OrderStatusValues


class InlineOrderCustomBotKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            ASK_QUESTION = "aq"
            PRE_CANCEL = "pc"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="oc", frozen=True)
        a: ActionEnum

        order_id: str = Field(alias="o")
        msg_id: int = Field(default=0, alias="m")
        chat_id: int = Field(default=0, alias="c")

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, order_id: str, msg_id: int, chat_id: int) -> str:
        return InlineOrderCustomBotKeyboard.Callback(
            a=action,
            order_id=order_id,
            msg_id=msg_id,
            chat_id=chat_id,
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineOrderCustomBotKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(order_id: str, msg_id: int = 0, chat_id: int = 0) -> InlineKeyboardMarkup:
        actions = InlineOrderCustomBotKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Задать вопрос",
                        callback_data=InlineOrderCustomBotKeyboard.callback_json(
                            actions.ASK_QUESTION, order_id, msg_id, chat_id
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Отменить заказ",
                        callback_data=InlineOrderCustomBotKeyboard.callback_json(
                            actions.PRE_CANCEL, order_id, msg_id, chat_id
                        ),
                    )
                ],
            ]
        )


class InlineOrderStatusesKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACKLOG = "bl"
            WAITING_PAYMENT = "wp"
            PROCESS = "ps"

            PRE_CANCEL = "pl"
            FINISH = "fh"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="os", frozen=True)
        a: ActionEnum

        order_id: str = Field(alias="o")
        msg_id: int = Field(default=0, alias="m")
        chat_id: int = Field(default=0, alias="c")

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, order_id: str, msg_id: int, chat_id: int) -> str:
        return InlineOrderStatusesKeyboard.Callback(
            a=action,
            order_id=order_id,
            msg_id=msg_id,
            chat_id=chat_id,
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineOrderStatusesKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(
        order_id: str, msg_id: int = 0, chat_id: int = 0, current_status: OrderStatusValues = OrderStatusValues.BACKLOG
    ) -> InlineKeyboardMarkup:
        actions = InlineOrderStatusesKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=("🔸 " if current_status == OrderStatusValues.BACKLOG else "") + "Ожидание",
                        callback_data=InlineOrderStatusesKeyboard.callback_json(
                            actions.BACKLOG, order_id, msg_id, chat_id
                        ),
                    ),
                    InlineKeyboardButton(
                        text=("🔸 " if current_status == OrderStatusValues.WAITING_PAYMENT else "") + "Ждет оплаты",
                        callback_data=InlineOrderStatusesKeyboard.callback_json(
                            actions.WAITING_PAYMENT, order_id, msg_id, chat_id
                        ),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=("🔸 " if current_status == OrderStatusValues.PROCESSING else "") + "Выполнять",
                        callback_data=InlineOrderStatusesKeyboard.callback_json(
                            actions.PROCESS, order_id, msg_id, chat_id
                        ),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Отменить ❌",
                        callback_data=InlineOrderStatusesKeyboard.callback_json(
                            actions.PRE_CANCEL, order_id, msg_id, chat_id
                        ),
                    ),
                    InlineKeyboardButton(
                        text="Завершить ✅",
                        callback_data=InlineOrderStatusesKeyboard.callback_json(
                            actions.FINISH, order_id, msg_id, chat_id
                        ),
                    ),
                ],
            ]
        )


class InlineOrderCancelKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CANCEL = "c"
            BACK_TO_ORDER_STATUSES = "bto"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="oc", frozen=True)
        a: ActionEnum

        order_id: str = Field(alias="o")
        msg_id: int = Field(default=0, alias="m")
        chat_id: int = Field(default=0, alias="c")

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, order_id: str, msg_id: int, chat_id: int) -> str:
        return InlineOrderCancelKeyboard.Callback(
            a=action,
            order_id=order_id,
            msg_id=msg_id,
            chat_id=chat_id,
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineOrderCancelKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(order_id: str, msg_id: int = 0, chat_id: int = 0) -> InlineKeyboardMarkup:
        actions = InlineOrderCancelKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Точно отменить?",
                        callback_data=InlineOrderCancelKeyboard.callback_json(
                            actions.CANCEL, order_id, msg_id, chat_id
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineOrderCancelKeyboard.callback_json(
                            actions.BACK_TO_ORDER_STATUSES, order_id, msg_id, chat_id
                        ),
                    )
                ],
            ]
        )


class InlineCreateReviewKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CREATE_REVIEW = "cr"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="or", frozen=True)
        a: ActionEnum

        order_id: str = Field(alias="o")
        chat_id: int = Field(default=0, alias="c")

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, order_id: str, chat_id: int) -> str:
        return InlineCreateReviewKeyboard.Callback(
            a=action,
            order_id=order_id,
            chat_id=chat_id,
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineCreateReviewKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(
        order_id: str,
        chat_id: int = 0,
    ) -> InlineKeyboardMarkup:
        actions = InlineCreateReviewKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Оставить отзыв",
                        callback_data=InlineCreateReviewKeyboard.callback_json(
                            actions.CREATE_REVIEW, order_id, chat_id
                        ),
                    )
                ],
            ]
        )


class InlineAcceptReviewKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SAVE = "sr"
            IGNORE = "ir"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="sir", frozen=True)
        a: ActionEnum

        product_review_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, product_review_id: int) -> str:
        return InlineAcceptReviewKeyboard.Callback(a=action, product_review_id=product_review_id).model_dump_json(
            by_alias=True
        )

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineAcceptReviewKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(product_review_id: int) -> InlineKeyboardMarkup:
        actions = InlineAcceptReviewKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Сохранить",
                        callback_data=InlineAcceptReviewKeyboard.callback_json(actions.SAVE, product_review_id),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Игнорировать",
                        callback_data=InlineAcceptReviewKeyboard.callback_json(actions.IGNORE, product_review_id),
                    )
                ],
            ],
        )
