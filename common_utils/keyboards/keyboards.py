from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from common_utils.keyboards.keyboard_utils import callback_json_validator, get_bot_channels, get_bot_username, \
    get_bot_mailing, get_bot_status, make_product_deep_link_url, make_product_webapp_info, get_bot_order_options, \
    make_webapp_info

from database.config import user_role_db, order_option_db, order_choose_option_db, option_db, bot_db
from database.models.user_role_model import UserRoleValues
from database.models.bot_model import BotPaymentTypeValues
from database.models.option_model import CurrencyCodesValues
from database.models.order_option_model import OrderOptionTypeValues, UnknownOrderOptionType


class InlineBotMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CHANNEL_LIST = "channels"

            MAILING_ADD = "mailing_create"
            MAILING_OPEN = "mailing_menu"

            BOT_SETTINGS = "settings"
            ADMINS = "admins"

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
                text="⚙️ Меню бота",
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
            EDIT_BG_COLOR = "edit_color"
            EDIT_ORDER_OPTIONS = "edit_ord_op"
            PAYMENT_METHOD = "payment_method"

            BACK_TO_BOT_MENU = "back_menu"

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
                        text="🎨 Изменить цвет фона",
                        callback_data=InlineBotSettingsMenuKeyboard.callback_json(
                            actions.EDIT_BG_COLOR, bot_id
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
                        text="💳 Изменить способ оплаты",
                        callback_data=InlineBotSettingsMenuKeyboard.callback_json(
                            actions.PAYMENT_METHOD, bot_id
                        )
                    ),
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


class InlineBotEditOrderOptionsKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            EDIT_ORDER_OPTION = "eoo"
            ADD_ORDER_OPTION = "aoo"

            BACK_TO_BOT_MENU = "b"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot_order_options", frozen=True)
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


class InlineEditOrderChooseOptionKeyboard:
    class Callback(BaseModel):

        class ActionEnum(Enum):
            EDIT_CHOOSE_OPTION_NAME = "econn"
            DELETE_CHOOSE_OPTION = "dcon"

            BACK_TO_ORDER_TYPE_MENU = "btoon"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bmn", frozen=True)
        a: ActionEnum

        bot_id: int
        opt_id: int
        choose_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int, opt_id: int, choose_id: int) -> str:
        return InlineEditOrderChooseOptionKeyboard.Callback(
            a=action, bot_id=bot_id, opt_id=opt_id, choose_id=choose_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineEditOrderChooseOptionKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(bot_id: int, order_option_id: int, order_choose_option_id: int) -> InlineKeyboardMarkup:
        actions = InlineEditOrderChooseOptionKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="Редактировать текст варианта",
                    callback_data=InlineEditOrderChooseOptionKeyboard.callback_json(
                        actions.EDIT_CHOOSE_OPTION_NAME, bot_id, order_option_id, order_choose_option_id)
                )],
                [InlineKeyboardButton(
                    text="Удалить вариант",
                    callback_data=InlineEditOrderChooseOptionKeyboard.callback_json(
                        actions.DELETE_CHOOSE_OPTION, bot_id, order_option_id, order_choose_option_id)
                )],
                [InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlineEditOrderChooseOptionKeyboard.callback_json(
                        actions.BACK_TO_ORDER_TYPE_MENU, bot_id, order_option_id, order_choose_option_id)
                )]
            ]
        )


class InlineEditOrderOptionTypeKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            EDIT_OPTION_TYPE = "eot"
            EDIT_CHOOSE_OPTION = "econ"
            ADD_CHOOSE_OPTION = "adco"

            BACK_TO_ORDER_OPTION = "b"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bm", frozen=True)
        a: ActionEnum

        bot_id: int
        opt_id: int
        choose_id: int | None

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int, opt_id: int, choose_id: int | None = None) -> str:
        return InlineEditOrderOptionTypeKeyboard.Callback(
            a=action, bot_id=bot_id, opt_id=opt_id, choose_id=choose_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineEditOrderOptionTypeKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(bot_id: int, order_option_id: int) -> InlineKeyboardMarkup:
        actions = InlineEditOrderOptionTypeKeyboard.Callback.ActionEnum
        oo = await order_option_db.get_order_option(order_option_id)

        choose_option_buttons = []

        match oo.option_type:
            case OrderOptionTypeValues.TEXT:
                status_btn = InlineKeyboardButton(
                    text="Изменить тип на choose",
                    callback_data=InlineEditOrderOptionTypeKeyboard.callback_json(
                        actions.EDIT_OPTION_TYPE, bot_id, order_option_id)
                )
            case OrderOptionTypeValues.CHOOSE:
                status_btn = InlineKeyboardButton(
                    text="Изменить тип на text",
                    callback_data=InlineEditOrderOptionTypeKeyboard.callback_json(
                        actions.EDIT_OPTION_TYPE, bot_id, order_option_id)
                )
                order_choose_options = await order_choose_option_db.get_all_choose_options(oo.id)
                for choose_option in order_choose_options:
                    choose_option_buttons.append(
                        [InlineKeyboardButton(
                            text=choose_option.choose_option_name,
                            callback_data=InlineEditOrderOptionTypeKeyboard.callback_json(
                                actions.EDIT_CHOOSE_OPTION, bot_id, order_option_id, choose_option.id
                            )
                        )]
                    )
                choose_option_buttons.append(
                    [InlineKeyboardButton(
                        text="Добавить опцию выбора",
                        callback_data=InlineEditOrderOptionTypeKeyboard.callback_json(
                            actions.ADD_CHOOSE_OPTION, bot_id, order_option_id
                        )
                    )]
                )
            case _:
                raise UnknownOrderOptionType(option_type=oo.option_type, bot_id=bot_id, order_option_id=order_option_id)

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [status_btn],
                *choose_option_buttons,
                [InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlineEditOrderOptionTypeKeyboard.callback_json(
                        actions.BACK_TO_ORDER_OPTION, bot_id, order_option_id
                    )
                )]
            ]
        )


class InlineBotEditOrderOptionKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            EDIT_OPTION_NAME = "eon"
            EDIT_EMOJI = "ee"
            EDIT_POSITION_INDEX = "epi"
            EDIT_REQUIRED_STATUS = "ers"
            EDIT_ORDER_OPTION_TYPE = "eopt"
            DELETE_ORDER_OPTION = "doo"

            BACK_TO_ORDER_OPTIONS = "boo"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot_edit_oo", frozen=True)
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

    @staticmethod
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
                        text="Редактировать тип опции",
                        callback_data=InlineBotEditOrderOptionKeyboard.callback_json(
                            actions.EDIT_ORDER_OPTION_TYPE, bot_id, order_option_id)
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


class InlinePaymentSettingsKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            MANUAL_METHOD = "manual"
            BOT_EDIT_POST_ORDER_MESSAGE = "pom"
            TG_PROVIDER = "tg_provider"
            TG_PROVIDER_SETUP = "setup_tg_pay"
            STARS = "stars"
            STARS_SETUP = "stars_setup"
            SELECT_CURRENCY = "currency"

            BACK_TO_BOT_MENU = "back"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="bot_payment_settings", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlinePaymentSettingsKeyboard.Callback(
            a=action, bot_id=bot_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlinePaymentSettingsKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(bot_id: int, selected_variant: BotPaymentTypeValues) -> InlineKeyboardMarkup:
        actions = InlinePaymentSettingsKeyboard.Callback.ActionEnum

        keyboard_buttons = [
            [
                InlineKeyboardButton(
                    text="🤝 Ручная оплата" +
                         f"{' ✅' if selected_variant == BotPaymentTypeValues.MANUAL else ''}",
                    callback_data=InlinePaymentSettingsKeyboard.callback_json(
                        actions.MANUAL_METHOD, bot_id
                    )
                )
            ],
        ]
        keyboard_buttons += [
            [
                InlineKeyboardButton(
                    text="📱 через телеграм (физ. товары)" +
                         f"{' ✅' if selected_variant == BotPaymentTypeValues.TG_PROVIDER else ''}",
                    callback_data=InlinePaymentSettingsKeyboard.callback_json(
                        actions.TG_PROVIDER, bot_id
                    )
                )
            ],
        ]
        keyboard_buttons += [
            [
                InlineKeyboardButton(
                    text="⭐️ Оплата в stars (цифр. товары)" +
                         f"{' ✅' if selected_variant == BotPaymentTypeValues.STARS else ''}",
                    callback_data=InlinePaymentSettingsKeyboard.callback_json(
                        actions.STARS, bot_id
                    )
                )
            ],
        ]
        if selected_variant == BotPaymentTypeValues.MANUAL:
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text="💳 Платежная информация",
                        callback_data=InlinePaymentSettingsKeyboard.callback_json(
                            actions.BOT_EDIT_POST_ORDER_MESSAGE, bot_id
                        )
                    )
                ],
            )
        if selected_variant == BotPaymentTypeValues.TG_PROVIDER:
            keyboard_buttons.append([
                InlineKeyboardButton(text="⚙️ Настроить встроенные платежи",
                                     callback_data=InlinePaymentSettingsKeyboard.callback_json(
                                         actions.TG_PROVIDER_SETUP, bot_id
                                     ))
            ])
        if selected_variant == BotPaymentTypeValues.STARS:
            keyboard_buttons.append([
                InlineKeyboardButton(text="⚙️ Настроить меню платежей в звездах",
                                     callback_data=InlinePaymentSettingsKeyboard.callback_json(
                                         actions.STARS_SETUP, bot_id
                                     ))
            ])
        keyboard_buttons += [
            [
                InlineKeyboardButton(
                    text="💱 Выбрать валюту магазина",
                    callback_data=InlinePaymentSettingsKeyboard.callback_json(
                        actions.SELECT_CURRENCY, bot_id
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlinePaymentSettingsKeyboard.callback_json(
                        actions.BACK_TO_BOT_MENU, bot_id
                    )
                )
            ],
        ]

        return InlineKeyboardMarkup(
            inline_keyboard=keyboard_buttons
        )


class InlineCurrencySelectKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            RUB = "rub"
            USD = "usd"
            EUR = "eur"
            ISL = "ils"

            BACK_TO_PAYMENT_MENU = "back_pay"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="select_currency", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlineCurrencySelectKeyboard.Callback(
            a=action, bot_id=bot_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineCurrencySelectKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(bot_id: int, selected_variant: CurrencyCodesValues) -> InlineKeyboardMarkup:
        actions = InlineCurrencySelectKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{'🔘' if selected_variant == CurrencyCodesValues.RUSSIAN_RUBLE else '⚪️'} RUB",
                        callback_data=InlineCurrencySelectKeyboard.callback_json(
                            actions.RUB, bot_id
                        )
                    ),
                    InlineKeyboardButton(
                        text=f"{'🔘' if selected_variant == CurrencyCodesValues.US_DOLLAR else '⚪️'} USD",
                        callback_data=InlineCurrencySelectKeyboard.callback_json(
                            actions.USD, bot_id
                        )
                    ),
                    InlineKeyboardButton(
                        text=f"{'🔘' if selected_variant == CurrencyCodesValues.EURO else '⚪️'} EUR",
                        callback_data=InlineCurrencySelectKeyboard.callback_json(
                            actions.EUR, bot_id
                        )
                    ),
                    InlineKeyboardButton(
                        text=f"{'🔘' if selected_variant == CurrencyCodesValues.ISRAELI_SHEQEL else '⚪️'} ILS",
                        callback_data=InlineCurrencySelectKeyboard.callback_json(
                            actions.ISL, bot_id
                        )
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineCurrencySelectKeyboard.callback_json(
                            actions.BACK_TO_PAYMENT_MENU, bot_id
                        )
                    )
                ],
            ]
        )


class InlinePaymentSetupKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            NAME = "name"
            EMAIL = "email"
            PHONE = "phone"
            SHIPPING = "address"

            PHOTO = "photo"
            WEBVIEW = "webview"

            SET_PROVIDER_TOKEN = "token"
            SHOW_PAYMENT = "show"
            SEND_TO_BOT = "send_to_bot"

            BACK_TO_PAYMENT_MENU = "back_pay"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="setup_payment_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, bot_id: int) -> str:
        return InlinePaymentSetupKeyboard.Callback(
            a=action, bot_id=bot_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlinePaymentSetupKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(bot_id: int, options_id: int, stars: bool = False) -> InlineKeyboardMarkup:
        actions = InlinePaymentSetupKeyboard.Callback.ActionEnum

        custom_bot = await bot_db.get_bot(bot_id)
        custom_bot_option = await option_db.get_option(options_id)

        if not stars:
            keyboard_buttons = [
                [
                    InlineKeyboardButton(
                        text=f"Просить имя{' ✅' if custom_bot_option.request_name_in_payment else ''}",
                        callback_data=InlinePaymentSetupKeyboard.callback_json(
                            actions.NAME, bot_id
                        )
                    ),
                    InlineKeyboardButton(
                        text=f"Просить почту{' ✅' if custom_bot_option.request_email_in_payment else ''}",
                        callback_data=InlinePaymentSetupKeyboard.callback_json(
                            actions.EMAIL, bot_id
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f"Просить телефон{' ✅' if custom_bot_option.request_phone_in_payment else ''}",
                        callback_data=InlinePaymentSetupKeyboard.callback_json(
                            actions.PHONE, bot_id
                        )
                    ),
                    InlineKeyboardButton(
                        text=f"Просить адрес{' ✅' if custom_bot_option.request_address_in_payment else ''}",
                        callback_data=InlinePaymentSetupKeyboard.callback_json(
                            actions.SHIPPING, bot_id
                        )
                    )
                ],
            ]
        else:
            keyboard_buttons = []

        keyboard_buttons += [
            [
                InlineKeyboardButton(
                    text=f"Фото заказа{' ✅' if custom_bot_option.show_photo_in_payment else ''}",
                    callback_data=InlinePaymentSetupKeyboard.callback_json(
                        actions.PHOTO, bot_id
                    )
                ),
                InlineKeyboardButton(
                    text=f"WebView{' ✅' if custom_bot_option.show_payment_in_webview else ''}",
                    callback_data=InlinePaymentSetupKeyboard.callback_json(
                        actions.WEBVIEW, bot_id
                    )
                )
            ],
        ]
        if not stars:
            keyboard_buttons += [
                [
                    InlineKeyboardButton(
                        text=f"🔐 Provider Token{' ✅' if custom_bot.provider_token else ''}",
                        callback_data=InlinePaymentSetupKeyboard.callback_json(
                            actions.SET_PROVIDER_TOKEN, bot_id
                        )
                    )
                ],
            ]
        keyboard_buttons += [
            [
                InlineKeyboardButton(
                    text=f"👀 Посмотреть платеж",
                    callback_data=InlinePaymentSetupKeyboard.callback_json(
                        actions.SHOW_PAYMENT, bot_id
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📩 Отправить в Вашего бота",
                    callback_data=InlinePaymentSetupKeyboard.callback_json(
                        actions.SEND_TO_BOT, bot_id
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlinePaymentSetupKeyboard.callback_json(
                        actions.BACK_TO_PAYMENT_MENU, bot_id
                    )
                )
            ],
        ]

        return InlineKeyboardMarkup(
            inline_keyboard=keyboard_buttons
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


class InlineBotMainWebAppButton:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SHOP = "🛍 Открыть магазин"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="inline_main_web_app", frozen=True)
        a: ActionEnum

    @staticmethod
    def get_keyboard(bot_id: int) -> InlineKeyboardMarkup:
        actions = InlineBotMainWebAppButton.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=actions.SHOP.value,
                        web_app=make_webapp_info(bot_id)
                    )
                ],
            ]
        )
