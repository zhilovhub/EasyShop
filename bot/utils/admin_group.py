from aiogram.types import Message, User

from bot.main import bot, config, logger

from enum import Enum


class EventTypes(Enum):
    NEW_USER = "🆕 С ботом <b>@{}</b> завел диалог <b>новый пользователь</b>!\n\n" \
               "Его данные:\n" \
               "id = <b>{}</b>, username = @<b>{}</b>\n" \
               "Имя = <b>{}</b>"
    STARTED_TRIAL = "🍟 <b>@{}</b> (<b>{}</b>) принял <b>пробную</b> подписку! (<b>@{}</b>)"



async def send_event(user: User, event_type: EventTypes) -> None:
    try:
        bot_username = (await bot.get_me()).username
        message_text = ""
        match event_type:
            case EventTypes.NEW_USER:
                message_text = event_type.value.format(bot_username, user.id, user.username, user.full_name)
            case EventTypes.STARTED_TRIAL:
                message_text = event_type.value.format(user.username, user.id, bot_username)
        await bot.send_message(
            chat_id=config.ADMIN_GROUP_ID,
            text=message_text
        )
    except Exception as e:
        logger.info(e)
