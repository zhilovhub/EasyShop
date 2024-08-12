from enum import Enum

from aiogram import Bot
from aiogram.types import Message, User
from aiogram.utils.formatting import Text, Bold, Pre, Italic

from common_utils.bot_settings_config import BOT_PROPERTIES
from common_utils.config import common_settings, main_telegram_bot_settings

from logs.config import logger


main_bot = Bot(main_telegram_bot_settings.TELEGRAM_TOKEN, default=BOT_PROPERTIES)


class UnknownEventTypeError(Exception):
    """Raises when provided unknown broadcasting event type"""


class EventTypes(Enum):
    # Admin Events Group
    # Main bot events
    NEW_USER = "new_user"
    STARTED_TRIAL_TRY = "stared_trial_try"
    STARTED_BIG_TRIAL_TRY = "started_big_trial_try"
    STARTED_TRIAL_SUCCESS = "stared_trial_success"
    SUBSCRIBED_PROCESS = "subscribed_process"
    SUBSCRIBED_SUCCESS = "subscribed_success"
    USER_CREATED_FIRST_BOT = "first_bot_creation"
    # Custom Bot events
    FIRST_ADMIN_MESSAGE = "first_admin_message"
    FIRST_USER_MESSAGE = "first_user_message"

    # Admin Bugs Group
    UNKNOWN_ERROR = "unknown"


def get_event_message_text(
        event_type: EventTypes,
        username: str | None = None,
        user_id: int | None = None,
        user_full_name: str | None = None,
        bot_username: str | None = None,
        error_message: str | None = None,
) -> Text:
    match event_type:
        case EventTypes.NEW_USER:
            text = Text(
                "🆕 С ботом ", Bold(f"@{bot_username}"),
                " завел диалог ", Bold("новый пользователь"), "!\n\n",
                "Его данные:",
                "\nid = ", Bold(f"{user_id}"),
                "\nusername = ", Bold(f"@{username}"),
                "\nИмя = ", Bold(f"{user_full_name}")
            )
        case EventTypes.STARTED_BIG_TRIAL_TRY:
            text = Text(
                "⚠ Пользователь ",
                Bold(f"@{username} "),
                Bold(f"({user_full_name})"),
                " пытается принять ",
                Bold("пробную"),
                " подписку на 30 дней",
            )
        case EventTypes.STARTED_TRIAL_TRY:
            text = Text(
                "⚠ Пользователь ",
                Bold(f"@{username} "),
                Bold(f"({user_full_name})"),
                " пытается принять ", Italic("пробную"), " подписку...",
            )
        case EventTypes.STARTED_TRIAL_SUCCESS:
            text = Text(
                "🍟 Пользователь ",
                Bold(f"@{username} "),
                Bold(f"({user_full_name})"),
                " ", Bold("принял"), " ", Italic("пробную"), " подписку!",
            )
        case EventTypes.SUBSCRIBED_PROCESS:
            text = Text(
                "⚠ Пользователь ",
                Bold(f"@{username} "),
                Bold(f"({user_full_name})"),
                " начал оформлять ", Italic("ПЛАТНУЮ"), " подписку...",
            )
        case EventTypes.SUBSCRIBED_SUCCESS:
            text = Text(
                "🎉✨✅ Пользователь ",
                Bold(f"@{username} "),
                Bold(f"({user_full_name})"),
                " ", Bold("принял"), " ", Italic("ПЛАТНУЮ"), " подписку!",
            )
        case EventTypes.USER_CREATED_FIRST_BOT:
            text = Text(
                "🤖 Пользователь впервые создал бота!\n\n",
                "👤 Данные:",
                "\nid = ", Bold(f"{user_id}"),
                "\nusername = ", Bold(f"@{username}"),
                "\nИмя = ", Bold(f"{user_full_name}"),
                "\n\nЮзернейм бота: ", Bold(f"@{bot_username}")
            )
        case EventTypes.FIRST_USER_MESSAGE:
            text = Text(
                "🆕📨 Пользовательскому боту (", Bold(f"@{bot_username}"), ") написал новый человек!\n\n",
                "👤 Данные:",
                "\nid = ", Bold(f"{user_id}"),
                "\nusername = ", Bold(f"@{username}"),
                "\nИмя = ", Bold(f"{user_full_name}"),
            )
        case EventTypes.FIRST_ADMIN_MESSAGE:
            text = Text(
                "📨 Администратор бота (", Bold(f"@{bot_username}"), ") впервые написал своему боту!\n\n",
                "👤 Данные админа:",
                "\nid = ", Bold(f"{user_id}"),
                "\nusername = ", Bold(f"@{username}"),
                "\nИмя = ", Bold(f"{user_full_name}"),
            )
        case EventTypes.UNKNOWN_ERROR:
            text = Text(
                "❗️ Произошла неизвестная ошибка при работе бота.\n\nBot: ", Bold(f"@{bot_username}"),
                "\n\nUsername: ", Bold(f"@{username}"),
                "\n\nUID: ", Bold(f"{user_id}"),
                "\n\nError message: \n", Pre(f"{error_message}"),
                )
        case _:
            raise UnknownEventTypeError
    return text


async def send_event(
        user: User,
        event_type: EventTypes,
        event_bot: Bot = main_bot,
        err_msg: str = 'Не указано'
) -> Message:
    try:
        bot_username = (await event_bot.get_me()).username
        message_text, message_entities = get_event_message_text(
            event_type=event_type,
            username=user.username,
            user_id=user.id,
            user_full_name=user.full_name,
            bot_username=bot_username,
            error_message=err_msg,
        ).render()

        match event_type:
            case (
                EventTypes.NEW_USER
                | EventTypes.SUBSCRIBED_SUCCESS
                | EventTypes.SUBSCRIBED_PROCESS
                | EventTypes.STARTED_TRIAL_SUCCESS
                | EventTypes.STARTED_TRIAL_TRY
                | EventTypes.USER_CREATED_FIRST_BOT
                | EventTypes.STARTED_BIG_TRIAL_TRY
            ):
                return await main_bot.send_message(
                    chat_id=common_settings.ADMIN_GROUP_ID,
                    text=message_text,
                    entities=message_entities,
                    parse_mode=None
                )
            case EventTypes.FIRST_ADMIN_MESSAGE | EventTypes.FIRST_USER_MESSAGE:
                return await main_bot.send_message(
                    chat_id=common_settings.ADMIN_GROUP_ID,
                    text=message_text,
                    entities=message_entities,
                    parse_mode=None
                )
            case EventTypes.UNKNOWN_ERROR:
                return await main_bot.send_message(
                    chat_id=common_settings.ADMIN_BUGS_GROUP_ID,
                    text=message_text,
                    entities=message_entities,
                    parse_mode=None
                )
            case _:
                raise UnknownEventTypeError
    except Exception as e:
        logger.warning(
            f"cant send event to admin group (event_type: {event_type}).", exc_info=e
        )
