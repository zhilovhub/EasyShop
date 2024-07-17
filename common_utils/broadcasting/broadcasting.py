from enum import Enum

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, User

from common_utils.env_config import ADMIN_GROUP_ID, TELEGRAM_TOKEN

from logs.config import logger


class EventTypes(Enum):
    NEW_USER = ("🆕 С ботом <b>@{}</b> завел диалог <b>новый пользователь</b>!\n\n"
                "Его данные:\n"
                "id = <b>{}</b>, username = @<b>{}</b>\n"
                "Имя = <b>{}</b>", None)
    STARTED_TRIAL = (
        "⚠ <b>@{}</b> (<b>{}</b>) пытается принять <b>пробную</b> подписку... (<b>@{}</b>)",
        "🍟 <b>@{}</b> (<b>{}</b>) принял <b>пробную</b> подписку! (<b>@{}</b>)"
    )
    SUBSCRIBED = (
        "⚠⚠ Для <b>@{}</b> (<b>{}</b>) оформляется <b>ПЛАТНАЯ</b> подписка... (<b>@{}</b>)",
        "🎉✨✅ <b>@{}</b> (<b>{}</b>) оформил <b>ПЛАТНУЮ</b> подписку! (<b>@{}</b>)"
    )
    UNKNOWN_ERROR = ("❗️ Произошла неизвестная ошибка при работе бота."
                     "\n\nBot: <b>@{}</b>"
                     "\n\nUsername: <b>{}</b>"
                     "\n\nUID: <b>{}</b>"
                     "\n\nError message: \n<code>{}</code>",
                     None)


async def send_event(
        user: User,
        event_type: EventTypes,
        event_bot: Bot = Bot(TELEGRAM_TOKEN),
        err_msg: str = 'Не указано'
) -> Message:
    try:
        bot_username = (await event_bot.get_me()).username
        message_text = ""
        event_type_text = event_type.value[0]
        match event_type:
            case EventTypes.NEW_USER:
                message_text = event_type_text.format(bot_username, user.id, user.username, user.full_name)
            case EventTypes.STARTED_TRIAL | EventTypes.SUBSCRIBED:
                message_text = event_type_text.format(user.username, user.id, bot_username)
            case EventTypes.UNKNOWN_ERROR:
                message_text = event_type_text.format(bot_username,
                                                      '@' + user.username if user.username else user.full_name,
                                                      user.id,
                                                      err_msg)
        return await event_bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=message_text
        )
    except Exception as e:
        logger.warning(
            f"cant send event to admin group (event_type: {event_type}).", exc_info=e
        )


async def success_event(user: User, event_bot: Bot, message: Message, event_type: EventTypes):
    try:
        bot_username = (await event_bot.get_me()).username
        message_text = ""
        event_type_text = event_type.value[1]
        match event_type:
            case EventTypes.NEW_USER:
                pass  # should be so
            case EventTypes.STARTED_TRIAL | EventTypes.SUBSCRIBED:
                message_text = event_type_text.format(user.username, user.id, bot_username)
        await message.edit_text(
            text=message_text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.warning(
            f"cant edit event message in admin group (event_type: {event_type}).", exc_info=e
        )
