from aiogram.enums import ParseMode
from aiogram.types import Message, User

from bot.main import bot, config, logger

from enum import Enum


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


async def send_event(user: User, event_type: EventTypes) -> Message:
    try:
        bot_username = (await bot.get_me()).username
        message_text = ""
        event_type_text = event_type.value[0]
        match event_type:
            case EventTypes.NEW_USER:
                message_text = event_type_text.format(bot_username, user.id, user.username, user.full_name)
            case EventTypes.STARTED_TRIAL | EventTypes.SUBSCRIBED:
                message_text = event_type_text.format(user.username, user.id, bot_username)
        return await bot.send_message(
            chat_id=config.ADMIN_GROUP_ID,
            text=message_text
        )
    except Exception:
        logger.warning(f"cant send event to admin group (event_type: {event_type}).", exc_info=True)


async def success_event(user: User, message: Message, event_type: EventTypes):
    try:
        bot_username = (await bot.get_me()).username
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
        logger.info(e)
