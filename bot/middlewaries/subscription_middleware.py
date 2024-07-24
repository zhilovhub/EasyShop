from typing import Callable, Dict, Any, Awaitable
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.main import subscription
from bot.utils.check_subscription import check_subscription

from common_utils.env_config import ADMINS
from common_utils.broadcasting.broadcasting import EventTypes, send_event

from database.config import user_db
from database.models.user_model import UserSchema, UserStatusValues, UserNotFoundError

from logs.config import logger


class CheckSubscriptionMiddleware(BaseMiddleware):
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
        except UserNotFoundError:
            logger.info(f"user {user_id} not found in db, creating new instance...")
            await send_event(event.from_user, EventTypes.NEW_USER)
            await user_db.add_user(UserSchema(
                user_id=user_id, username=event.from_user.username, registered_at=datetime.utcnow(),
                status=UserStatusValues.TRIAL, locale="default", subscribed_until=None)
            )
            logger.error(
                f"user_id={user_id}: DANGER! This place in middleware should not be called"
            )

        if user_id not in ADMINS and \
                not (await subscription.is_user_subscribed(user_id)) and \
                message.text not in ("/start", "/check_subscription"):
            if is_message:
                await message.answer("Для того, чтобы пользоваться ботом, тебе нужна подписка")
            else:
                await event.answer("Для того, чтобы пользоваться ботом, тебе нужна подписка", show_alert=True)
            return await check_subscription(message)

        return await handler(event, data)
