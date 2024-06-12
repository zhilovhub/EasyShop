from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject, User

from logs.config import logger, extra_params

import redis


class MainLogMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.redis = redis.Redis()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]) -> Any:

        try:
            user: User = data["event_from_user"]
            state: FSMContext = data["state"]
            raw_state: FSMContext = data["raw_state"]

            state_data = await state.get_data()
            callback_info = f"New event: user_id={user.id}, @{user.username}, {raw_state}, {state_data}"

            if isinstance(event, Message):
                if self.redis.get(str(event.message_id)) is None:
                    logger.info(
                        f"{callback_info} has written {event.text}",
                        extra=extra_params(user_id=user.id)
                    )
                    # noinspection PyAsyncCall
                    self.redis.set(name=str(event.message_id), value="", ex=2)
            elif isinstance(event, CallbackQuery):
                if self.redis.get(str(event.id)) is None:
                    logger.info(
                            f"{callback_info} has sent callback_data {event.data}",
                            extra=extra_params(user_id=user.id)
                        )
                    # noinspection PyAsyncCall
                    self.redis.set(name=str(event.id), value="", ex=2)
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
