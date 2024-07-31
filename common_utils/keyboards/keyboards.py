from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from common_utils.keyboards.keyboard_utils import callback_json_validator, get_bot_channels, get_bot_username, \
    get_bot_mailing, get_bot_status, make_product_deep_link_url, make_product_webapp_info, get_bot_order_options

from database.config import bot_db, user_role_db, order_option_db
from database.models.user_role_model import UserRoleValues, UserRoleSchema, UserRoleNotFoundError

from logs.config import logger, extra_params


class InlineBotMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CHANNEL_LIST = "channels"

            MAILING_ADD = "mailing_create"
            MAILING_OPEN = "mailing_menu"

            BOT_SETTINGS = "settings"
            ADMINS = "admins"
            BOT_EDIT_POST_ORDER_MESSAGE = "pom"

            BOT_STOP = "stop_bot"
            BOT_START = "start_bot"

            BOT_STATISTICS = "statistic"
            BOT_GOODS_OPEN = "goods"

            PARTNERSHIP = "partnership"

            LEAVE_ADMINISTRATING = "leave_admin"

            BOT_DELETE = "delete_bot"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlineBotMenuKeyboard.Callback(
            a=action, bot_id=bot_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineBotMenuKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(bot_id: int, user_id: int) -> InlineKeyboardMarkup:
        actions = InlineBotMenuKeyboard.Callback.ActionEnum

        user_role = await user_role_db.get_user_role(user_id, bot_id)

        channel_inline_button = InlineKeyboardButton(
            text="📢 Добавить в канал",
            url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel"
        ) if not await get_bot_channels(bot_id=bot_id) else \
            InlineKeyboardButton(
                text="📢 Каналы бота",
                callback_data=InlineBotMenuKeyboard.callback_json(
                    actions.CHANNEL_LIST, bot_id
                )
        )

        mailing_inline_button = InlineKeyboardButton(
            text="💌 Создать рассылку в ЛС",
            callback_data=InlineBotMenuKeyboard.callback_json(
                actions.MAILING_ADD, bot_id
            ),
        ) if not await get_bot_mailing(bot_id=bot_id) else \
            InlineKeyboardButton(
                text="💌 Рассылка в ЛС",
                callback_data=InlineBotMenuKeyboard.callback_json(
                    actions.MAILING_OPEN, bot_id
                )
        )

        leave_admin_or_delete_bot_button = InlineKeyboardButton(
            text="🗑 Удалить бота",
            callback_data=InlineBotMenuKeyboard.callback_json(
                actions.BOT_DELETE, bot_id
            )
        ) if user_role.role == UserRoleValues.OWNER else \
            InlineKeyboardButton(
                text="🛑 Покинуть администрирование",
                callback_data=InlineBotMenuKeyboard.callback_json(
                    actions.LEAVE_ADMINISTRATING, bot_id
                )
        )

        bot_setup_buttons = [
            InlineKeyboardButton(
                text="⚙️ Настройки бота",
                callback_data=InlineBotMenuKeyboard.callback_json(
                    actions.BOT_SETTINGS, bot_id
                )
            ),
            InlineKeyboardButton(
                text="👥 Администраторы",
                callback_data=InlineBotMenuKeyboard.callback_json(
                    actions.ADMINS, bot_id
                )
            ),
        ] if user_role.role == UserRoleValues.OWNER else \
            [
                InlineKeyboardButton(
                    text="⚙️ Настройки бота",
                    callback_data=InlineBotMenuKeyboard.callback_json(
                        actions.BOT_SETTINGS, bot_id
                    )
                ),
        ]

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Платежная информация",
                        callback_data=InlineBotMenuKeyboard.callback_json(
                            actions.BOT_EDIT_POST_ORDER_MESSAGE, bot_id
                        )
                    )
                ],
                bot_setup_buttons,
                [
                    InlineKeyboardButton(
                        text="⛔ Остановить бота",
                        callback_data=InlineBotMenuKeyboard.callback_json(
                            actions.BOT_STOP, bot_id
                        )
                    ) if await get_bot_status(bot_id) == "online" else InlineKeyboardButton(
                        text="🚀 Запустить бота",
                        callback_data=InlineBotMenuKeyboard.callback_json(
                            actions.BOT_START, bot_id
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Статистика",
                        callback_data=InlineBotMenuKeyboard.callback_json(
                            actions.BOT_STATISTICS, bot_id
                        ),
                    ),
                    InlineKeyboardButton(
                        text="📦 Мои товары",
                        callback_data=InlineBotMenuKeyboard.callback_json(
                            actions.BOT_GOODS_OPEN, bot_id
                        ),
                    )
                ],
                [
                    channel_inline_button
                ],
                [
                    mailing_inline_button,
                ],
                [
                    InlineKeyboardButton(
                        text="🤝 Партнерство",
                        callback_data=InlineBotMenuKeyboard.callback_json(
                            actions.PARTNERSHIP, bot_id
                        )
                    )
                ],
                [
                    leave_admin_or_delete_bot_button,
                ],
            ],
        )


class InlineBotSettingsMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BOT_EDIT_HELLO_TEXT = "start_text"
            BOT_EDIT_EXPLANATION_TEXT = "explain_text"
            EDIT_THEME = "edit_theme"
            EDIT_ORDER_OPTIONS = "edit_ord_op"

            BACK_TO_BOT_MENU = "back"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot__settings_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlineBotSettingsMenuKeyboard.Callback(
            a=action, bot_id=bot_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineBotSettingsMenuKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(bot_id: int) -> InlineKeyboardMarkup:
        actions = InlineBotSettingsMenuKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👋 Приветственный текст",
                        callback_data=InlineBotSettingsMenuKeyboard.callback_json(
                            actions.BOT_EDIT_HELLO_TEXT, bot_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🗣 Текст объяснения",
                        callback_data=InlineBotSettingsMenuKeyboard.callback_json(
                            actions.BOT_EDIT_EXPLANATION_TEXT, bot_id
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎨 Изменить цвета магазина",
                        callback_data=InlineBotSettingsMenuKeyboard.callback_json(
                            actions.EDIT_THEME, bot_id
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚙️ Редактировать опции заказа",
                        callback_data=InlineBotSettingsMenuKeyboard.callback_json(
                            actions.EDIT_ORDER_OPTIONS, bot_id
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineBotSettingsMenuKeyboard.callback_json(
                            actions.BACK_TO_BOT_MENU, bot_id
                        )
                    )
                ],
            ]
        )


class InlineThemeSettingsMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CHOOSE_PRESET = "presets"
            CUSTOM_COLORS = "custom_colors"

            BACK_TO_BOT_SETTINGS = "back_settings"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot_customization_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlineThemeSettingsMenuKeyboard.Callback(
            a=action, bot_id=bot_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineThemeSettingsMenuKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(bot_id: int) -> InlineKeyboardMarkup:
        actions = InlineThemeSettingsMenuKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📚 Выбрать тему",
                        callback_data=InlineThemeSettingsMenuKeyboard.callback_json(
                            actions.CHOOSE_PRESET, bot_id
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🖍 Изменить цвета вручную",
                        callback_data=InlineThemeSettingsMenuKeyboard.callback_json(
                            actions.CUSTOM_COLORS, bot_id
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineThemeSettingsMenuKeyboard.callback_json(
                            actions.BACK_TO_BOT_SETTINGS, bot_id
                        )
                    )
                ],
            ]
        )


class InlineBotEditOrderOptionsKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            EDIT_ORDER_OPTION = "eoo"
            ADD_ORDER_OPTION = "aoo"

            BACK_TO_BOT_MENU = "b"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot_menu", frozen=True)
        a: ActionEnum

        bot_id: int
        order_option_id: int | None

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int, order_option_id: int | None = None) -> str:
        return InlineBotEditOrderOptionsKeyboard.Callback(
            a=action, bot_id=bot_id, order_option_id=order_option_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineBotEditOrderOptionsKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(bot_id: int) -> InlineKeyboardMarkup:
        actions = InlineBotEditOrderOptionsKeyboard.Callback.ActionEnum
        order_options = await get_bot_order_options(bot_id)
        oo_btns = []
        for oo in order_options:
            oo_btns.append(
                [InlineKeyboardButton(
                    text=oo.option_name,
                    callback_data=InlineBotEditOrderOptionsKeyboard.callback_json(
                        actions.EDIT_ORDER_OPTION, bot_id, oo.id
                    )
                )]
            )
        return InlineKeyboardMarkup(
            inline_keyboard=[
                *oo_btns,
                [
                    InlineKeyboardButton(
                        text="🛠️ Создать новую опцию",
                        callback_data=InlineBotEditOrderOptionsKeyboard.callback_json(
                            actions.ADD_ORDER_OPTION, bot_id
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineBotEditOrderOptionsKeyboard.callback_json(
                            actions.BACK_TO_BOT_MENU, bot_id
                        )
                    )
                ],
            ]
        )


class InlineBotEditOrderOptionKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            EDIT_OPTION_NAME = "eon"
            EDIT_EMOJI = "ee"
            EDIT_POSITION_INDEX = "epi"
            EDIT_REQUIRED_STATUS = "ers"
            DELETE_ORDER_OPTION = "doo"

            BACK_TO_ORDER_OPTIONS = "boo"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot_menu", frozen=True)
        a: ActionEnum

        bot_id: int
        order_option_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int, order_option_id: int) -> str:
        return InlineBotEditOrderOptionKeyboard.Callback(
            a=action, bot_id=bot_id, order_option_id=order_option_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineBotEditOrderOptionKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    async def get_keyboard(bot_id: int, order_option_id: int) -> InlineKeyboardMarkup:
        actions = InlineBotEditOrderOptionKeyboard.Callback.ActionEnum
        oo = await order_option_db.get_order_option(order_option_id)
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Редактировать название",
                        callback_data=InlineBotEditOrderOptionKeyboard.callback_json(
                            actions.EDIT_OPTION_NAME, bot_id, order_option_id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Редактировать эмодзи",
                        callback_data=InlineBotEditOrderOptionKeyboard.callback_json(
                            actions.EDIT_EMOJI, bot_id, order_option_id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Обязательно " + ("✅" if oo.required else "❌"),
                        callback_data=InlineBotEditOrderOptionKeyboard.callback_json(
                            actions.EDIT_REQUIRED_STATUS, bot_id, order_option_id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Редактировать позицию",
                        callback_data=InlineBotEditOrderOptionKeyboard.callback_json(
                            actions.EDIT_POSITION_INDEX, bot_id, order_option_id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Удалить",
                        callback_data=InlineBotEditOrderOptionKeyboard.callback_json(
                            actions.DELETE_ORDER_OPTION, bot_id, order_option_id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineBotEditOrderOptionKeyboard.callback_json(
                            actions.BACK_TO_ORDER_OPTIONS, bot_id, order_option_id)
                    )
                ]
            ]
        )


class InlineAdministratorsManageKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            ADD_ADMIN = "add"
            ADMIN_LIST = "list"

            BACK_TO_BOT_MENU = "back"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot_admins_manage_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlineAdministratorsManageKeyboard.Callback(
            a=action, bot_id=bot_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineAdministratorsManageKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(bot_id: int) -> InlineKeyboardMarkup:
        actions = InlineAdministratorsManageKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Добавить администратора",
                        callback_data=InlineAdministratorsManageKeyboard.callback_json(
                            actions.ADD_ADMIN, bot_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="👥 Список администраторов",
                        callback_data=InlineAdministratorsManageKeyboard.callback_json(
                            actions.ADMIN_LIST, bot_id
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineAdministratorsManageKeyboard.callback_json(
                            actions.BACK_TO_BOT_MENU, bot_id
                        )
                    )
                ],
            ]
        )


class InlineModeProductKeyboardButton:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SHOP = "🛍 Открыть страницу товара"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="inline_product_deep_link", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard(product_id: int, bot_username) -> InlineKeyboardMarkup:
        actions = InlineModeProductKeyboardButton.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=actions.SHOP.value,
                        url=make_product_deep_link_url(product_id, bot_username)
                    )
                ],
            ]
        )


class InlineCustomBotModeProductKeyboardButton:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SHOP = "🛍 Открыть страницу товара"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="inline_product_web_app", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard(product_id: int, bot_id: int) -> InlineKeyboardMarkup:
        actions = InlineCustomBotModeProductKeyboardButton.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=actions.SHOP.value,
                        web_app=make_product_webapp_info(product_id, bot_id)
                    )
                ],
            ]
        )
