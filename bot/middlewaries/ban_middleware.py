from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from database.config import user_db
from database.models.user_model import UserNotFoundError, UserStatusValues

from logs.config import logger


class BanCheckMiddleware(BaseMiddleware):
    """Middleware that checks if user is banned in main bot"""

    async def __call__(
        self,
        handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id

        try:
            user = await user_db.get_user(user_id)
            if user.status not in (UserStatusValues.BANNED,):
                return await handler(event, data)
            else:
                logger.debug(f"Banned user ({event.from_user}) try to use bot with event ({event}")
                return
        except UserNotFoundError:
            return await handler(event, data)
