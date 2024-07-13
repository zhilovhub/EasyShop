from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter

from bot.config import ADMINS

from logs.config import logger, extra_params


class IsAdmin(BaseFilter):
    def __init__(self):
        pass

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        if event.from_user.id in ADMINS:
            return True
        else:
            chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
            logger.debug(f"message to handler that uses only admin filter from non admin user "
                         f"(user_id: {event.from_user.id}, "
                         f"chat_id={chat_id})",
                         extra_params(user_id=event.from_user.id,
                                      chat_id=chat_id))
            return False
