from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.main import subscription
from bot.utils import MessageTexts
from bot.config import logger, ADMINS
from bot.exceptions import UserNotFound
from bot.handlers.routers import user_db
from bot.handlers.command_handlers import check_subscription_command_handler
from bot.utils.admin_group import send_event, EventTypes
from database.models.user_model import UserSchema, UserStatusValues


class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
            self,
            handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery | Message,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        message, is_message = (event, True) if isinstance(event, Message) else (event.message, False)
        try:
            await user_db.get_user(user_id)
        except UserNotFound:
            logger.info(f"user {user_id} not found in db, creating new instance...")
            await send_event(event.from_user, EventTypes.NEW_USER)
            await user_db.add_user(UserSchema(
                user_id=user_id, registered_at=datetime.utcnow(), status=UserStatusValues.NEW, locale="default",
                subscribed_until=None)
            )
            await message.answer(MessageTexts.ABOUT_MESSAGE.value)

        if user_id not in ADMINS and \
                not (await subscription.is_user_subscribed(user_id)) and \
                message.text not in ("/start", "/check_subscription"):
            if is_message:
                await message.answer("Для того, чтобы пользоваться ботом, тебе нужна подписка")
            else:
                await event.answer("Для того, чтобы пользоваться ботом, тебе нужна подписка", show_alert=True)
            return await check_subscription_command_handler(message)

        return await handler(event, data)
