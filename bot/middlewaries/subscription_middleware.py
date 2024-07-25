from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.main import subscription
from bot.utils.check_subscription import check_subscription

from common_utils.env_config import ADMINS


class CheckSubscriptionMiddleware(BaseMiddleware):
    """
    Middleware that doesn't allow user communicate to the bot without subscription

    Даем доступ, если пользователь:
    1. Админ
    2. Имеет статус TRIAL, SUBSCRIBED
    """

    async def __call__(
            self,
            handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery | Message,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        message, is_message = (event, True) if isinstance(event, Message) else (event.message, False)

        if user_id not in ADMINS and not (await subscription.is_user_subscribed(user_id)):
            # Пользователь не прошел ни по одному из заявленных критериев, уведомляем его об этом
            return await check_subscription(message)

        # Полноценный доступ открыт - исполняем хендлер
        return await handler(event, data)
