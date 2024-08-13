from enum import Enum

from pydantic import BaseModel, ValidationError, ConfigDict, Field

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from common_utils.make_webapp_info import make_admin_panel_webapp_info
from common_utils.keyboards.keyboard_utils import callback_json_validator


class ReplyBackStockMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK_TO_STOCK_MENU = "🔙 Назад"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="stock_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyBackStockMenuKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=actions.BACK_TO_STOCK_MENU.value)]], resize_keyboard=True
        )


class InlineWebStockKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            GOOD_LIST = "📋 Список товаров"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="gl", frozen=True)
        a: ActionEnum

    @staticmethod
    async def get_keyboard(bot_id: int) -> InlineKeyboardMarkup:
        actions = InlineWebStockKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=actions.GOOD_LIST.value, web_app=make_admin_panel_webapp_info(bot_id))]
            ]
        )


class InlineStockMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            GOODS_COUNT = "goods_count"
            ADD_GOOD = "add_good"

            GOODS_COUNT_MANAGE = "goods_count_manage"

            IMPORT = "import"
            EXPORT = "export"

            AUTO_REDUCE = "auto_reduce"

            BACK_TO_BOT_MENU = "back_to_menu"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="stock_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlineStockMenuKeyboard.Callback(a=action, bot_id=bot_id).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineStockMenuKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(bot_id: int, auto_reduce: bool = False) -> InlineKeyboardMarkup:
        actions = InlineStockMenuKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🧮 Количество товаров",
                        callback_data=InlineStockMenuKeyboard.callback_json(actions.GOODS_COUNT, bot_id),
                    ),
                    InlineKeyboardButton(text="📋 Список товаров", web_app=make_admin_panel_webapp_info(bot_id)),
                ],
                [
                    InlineKeyboardButton(
                        text="🆕 Добавить товар",
                        callback_data=InlineStockMenuKeyboard.callback_json(actions.ADD_GOOD, bot_id),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="⬆️ Экспорт товаров",
                        callback_data=InlineStockMenuKeyboard.callback_json(actions.EXPORT, bot_id),
                    ),
                    InlineKeyboardButton(
                        text="⬇️ Импорт товаров",
                        callback_data=InlineStockMenuKeyboard.callback_json(actions.IMPORT, bot_id),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="📦 Управление остатками",
                        callback_data=InlineStockMenuKeyboard.callback_json(actions.GOODS_COUNT_MANAGE, bot_id),
                    ),
                    InlineKeyboardButton(
                        text=f"{'✅' if auto_reduce else '❌'} Автоуменьшение на складе",
                        callback_data=InlineStockMenuKeyboard.callback_json(actions.AUTO_REDUCE, bot_id),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineStockMenuKeyboard.callback_json(actions.BACK_TO_BOT_MENU, bot_id),
                    ),
                ],
            ],
        )


class InlineStockImportMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            REPLACE_ALL = "replace_all"
            REPLACE_DUPLICATES = "replace_duplicates"
            NOT_REPLACE_DUPLICATES = "not_replace_duplicates"

            BACK_TO_STOCK_MENU = "back_to_stock_menu"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="import_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlineStockImportMenuKeyboard.Callback(a=action, bot_id=bot_id).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineStockImportMenuKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(bot_id: int) -> InlineKeyboardMarkup:
        actions = InlineStockImportMenuKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="1️⃣", callback_data=InlineStockImportMenuKeyboard.callback_json(actions.REPLACE_ALL, bot_id)
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="2️⃣",
                        callback_data=InlineStockImportMenuKeyboard.callback_json(actions.REPLACE_DUPLICATES, bot_id),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="3️⃣",
                        callback_data=InlineStockImportMenuKeyboard.callback_json(
                            actions.NOT_REPLACE_DUPLICATES, bot_id
                        ),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineStockImportMenuKeyboard.callback_json(actions.BACK_TO_STOCK_MENU, bot_id),
                    ),
                ],
            ],
        )


class InlineStockImportConfirmKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CONFIRM = "cfrm"
            DENY = "deny"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="if", frozen=True)
        a: ActionEnum

        bot_id: int = Field(alias="b")
        import_action: str = Field(alias="ia")
        file_type: str = Field(alias="t")

    @staticmethod
    @callback_json_validator
    def callback_json(
        action: Callback.ActionEnum,
        bot_id: int,
        import_action: str,
        file_type: str,
    ) -> str:
        return InlineStockImportConfirmKeyboard.Callback(
            a=action, bot_id=bot_id, import_action=import_action, file_type=file_type
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineStockImportConfirmKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(bot_id: int, import_action: str, file_type: str) -> InlineKeyboardMarkup:
        actions = InlineStockImportConfirmKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅",
                        callback_data=InlineStockImportConfirmKeyboard.callback_json(
                            actions.CONFIRM, bot_id, import_action, file_type
                        ),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="❌",
                        callback_data=InlineStockImportConfirmKeyboard.callback_json(
                            actions.DENY, bot_id, import_action, file_type
                        ),
                    )
                ],
            ]
        )


class InlineStockImportFileTypeKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            EXCEL = "xlsx"
            BACK_TO_STOCK_MENU = "btsm"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="i", frozen=True)
        a: ActionEnum

        bot_id: int = Field(alias="b")
        import_action: str = Field(alias="i")

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int, import_action: str) -> str:
        return InlineStockImportFileTypeKeyboard.Callback(
            a=action, bot_id=bot_id, import_action=import_action
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineStockImportFileTypeKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(bot_id: int, import_action: str) -> InlineKeyboardMarkup:
        actions = InlineStockImportFileTypeKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Excel (.xlsx)",
                        callback_data=InlineStockImportFileTypeKeyboard.callback_json(
                            actions.EXCEL, bot_id, import_action
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineStockImportFileTypeKeyboard.callback_json(
                            actions.BACK_TO_STOCK_MENU, bot_id, import_action
                        ),
                    )
                ],
            ]
        )
