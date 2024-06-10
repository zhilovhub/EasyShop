import asyncio
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated, TelegramObject, User

from bot.main import bot
from bot.utils.admin_group import send_event, EventTypes

from logs.config import logger, extra_params

from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter


class MainLogMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]) -> Any:
        print(data)

        # TODO cache by message_id

        try:
            user: User = data["event_from_user"]
            state: FSMContext = data["state"]
            raw_state: FSMContext = data["raw_state"]

            state_data = await state.get_data()
            callback_info = f"New event: user_id={user.id}, @{user.username}, {raw_state}, {state_data}"

            if isinstance(event, Message):
                logger.info(
                    f"{callback_info} has written {event.text}",
                    extra=extra_params(user_id=user.id)
                )
            elif isinstance(event, CallbackQuery):
                logger.info(
                    f"{callback_info} has sent callback_data {event.data}",
                    extra=extra_params(user_id=user.id)
                )
            else:
                logger.warning(
                    f"{callback_info} has sent unexpected event {event}",
                    extra=extra_params(user_id=user.id)
                )
        except Exception as e:
            logger.error(
                "New event: logger error",
                exc_info=e
            )

        return await handler(event, data)
