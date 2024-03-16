from aiogram.types import Message

from bot.main import bot, config, logger

from enum import Enum


class EventTypes(Enum):
    NEW_USER = "С ботом <b>@{}</b> завел диалог новый пользователь!\n\n" \
               "Его данные:\n" \
               "id = <b>{}</b>, username = @<b>{}</b>\n" \
               "Имя = <b>{}</b>"


async def send_event(message: Message, event_type: EventTypes) -> None:
    try:
        user = message.from_user
        bot_username = (await bot.get_me()).username
        match event_type:
            case EventTypes.NEW_USER:
                await bot.send_message(
                    chat_id=config.ADMIN_GROUP_ID,
                    text=event_type.value.format(bot_username, user.id, user.username, user.full_name)
                )
    except Exception as e:
        logger.info(e)
