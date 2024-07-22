from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from common_utils.keyboards.keyboard_utils import callback_json_validator, get_bot_channels, get_bot_username, \
    get_bot_mailing, get_bot_status

from database.config import bot_db, user_role_db
from database.models.user_role_model import UserRoleValues, UserRoleSchema

from logs.config import logger, extra_params


class InlineBotMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CHANNEL_LIST = "channels"

            MAILING_ADD = "mailing_create"
            MAILING_OPEN = "mailing_menu"

            BOT_SETTINGS = "settings"
            ADMINS = "settings"
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

        # TODO ? remove after updating old users
        try:
            user_role = await user_role_db.get_user_role(user_id, bot_id)
        except:
            logger.debug(
                f"user_id={user_id} bot_id={bot_id}: role not found, auto creating new role",
                extra=extra_params(user_id=user_id, bot_id=bot_id))
            bot = await bot_db.get_bot(bot_id)
            if bot.created_by == user_id:
                role = UserRoleValues.OWNER
            else:
                role = UserRoleValues.ADMINISTRATOR
            await user_role_db.add_user_role(UserRoleSchema(user_id=user_id, bot_id=bot_id, role=role))
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
            EDIT_BG_COLOR = "edit_color"

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
                        text="🎨 Изменить цвет фона",
                        callback_data=InlineBotSettingsMenuKeyboard.callback_json(
                            actions.EDIT_BG_COLOR, bot_id
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
