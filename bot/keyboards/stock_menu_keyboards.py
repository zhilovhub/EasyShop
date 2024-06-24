from enum import Enum

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from pydantic import BaseModel, ValidationError, ConfigDict, Field

from bot.utils import make_admin_panel_webapp_info


class ReplyBackStockMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK_TO_STOCK_MENU = "🔙 Назад"

        model_config = ConfigDict(from_attributes=True)

        n: str = Field(default="stock_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyBackStockMenuKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=actions.BACK_TO_STOCK_MENU.value
                    )
                ]
            ], resize_keyboard=True
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

        model_config = ConfigDict(from_attributes=True)

        n: str = Field(default="stock_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlineStockMenuKeyboard.Callback(
            a=action, bot_id=bot_id
        ).model_dump_json()

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
                        callback_data=InlineStockMenuKeyboard.callback_json(
                            actions.GOODS_COUNT, bot_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="📋 Список товаров",
                        web_app=make_admin_panel_webapp_info(bot_id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆕 Добавить товар",
                        callback_data=InlineStockMenuKeyboard.callback_json(
                            actions.ADD_GOOD, bot_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="📦 Управление остатками",
                        callback_data=InlineStockMenuKeyboard.callback_json(
                            actions.GOODS_COUNT_MANAGE, bot_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="⬇️ Импорт товаров",
                        callback_data=InlineStockMenuKeyboard.callback_json(
                            actions.IMPORT, bot_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="⬆️ Экспорт товаров",
                        callback_data=InlineStockMenuKeyboard.callback_json(
                            actions.EXPORT, bot_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=f"{'✅' if auto_reduce else '❌'} Автоуменьшение на складе",
                        callback_data=InlineStockMenuKeyboard.callback_json(
                            actions.AUTO_REDUCE, bot_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineStockMenuKeyboard.callback_json(
                            actions.BACK_TO_BOT_MENU, bot_id
                        )
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

        model_config = ConfigDict(from_attributes=True)

        n: str = Field(default="import_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlineStockImportMenuKeyboard.Callback(
            a=action, bot_id=bot_id
        ).model_dump_json()

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
                        text="1",
                        callback_data=InlineStockImportMenuKeyboard.callback_json(
                            actions.REPLACE_ALL, bot_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="2",
                        callback_data=InlineStockImportMenuKeyboard.callback_json(
                            actions.REPLACE_DUPLICATES, bot_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="3",
                        callback_data=InlineStockImportMenuKeyboard.callback_json(
                            actions.NOT_REPLACE_DUPLICATES, bot_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineStockImportMenuKeyboard.callback_json(
                            actions.BACK_TO_STOCK_MENU, bot_id
                        )
                    ),
                ],
            ],
        )
