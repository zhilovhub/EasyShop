import redis

from typing import Callable, Dict, Any, Awaitable
from logging import Logger

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User, InlineQuery, PreCheckoutQuery
from aiogram.fsm.context import FSMContext

from logs.config import extra_params


class _MockRedis:
    """If connect to real Redis is broken"""

    def get(self, *args, **kwargs) -> None:  # noqa
        return None

    def set(self, *args, **kwargs) -> None:
        pass


class LogMiddleware(BaseMiddleware):
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        try:
            self.redis = redis.Redis()
            self.redis.info()
        except redis.ConnectionError as e:
            self.redis = _MockRedis()
            self.logger.warning("Unable to connect to Redis", exc_info=e)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            user: User = data["event_from_user"]
            state: FSMContext = data["state"]
            raw_state: FSMContext = data["raw_state"]

            state_data = await state.get_data()
            callback_info = f"New event: user_id={user.id}, @{user.username}, {raw_state}, {state_data}"

            if isinstance(event, Message):
                if self.redis.get(str(event.message_id)) is None:
                    self.logger.info(f"{callback_info} has written {event.text}", extra=extra_params(user_id=user.id))
                    # noinspection PyAsyncCall
                    self.redis.set(name=str(event.message_id), value="", ex=2)
            elif isinstance(event, CallbackQuery):
                if self.redis.get(str(event.id)) is None:
                    self.logger.info(
                        f"{callback_info} has sent callback_data {event.data}", extra=extra_params(user_id=user.id)
                    )
                    # noinspection PyAsyncCall
                    self.redis.set(name=str(event.id), value="", ex=2)
            elif isinstance(event, InlineQuery):
                if self.redis.get(str(event.id)) is None:
                    self.logger.info(
                        f"{callback_info} has sent inline_query {event.query}", extra=extra_params(user_id=user.id)
                    )
                    # noinspection PyAsyncCall
                    self.redis.set(name=str(event.id), value="", ex=2)
            elif isinstance(event, PreCheckoutQuery):
                if self.redis.get(str(event.id)) is None:
                    self.logger.info(
                        f"{callback_info} has sent pre_checkout_query with payload {event.invoice_payload}",
                        extra=extra_params(user_id=user.id),
                    )
                    # noinspection PyAsyncCall
                    self.redis.set(name=str(event.id), value="", ex=2)
            else:
                self.logger.warning(
                    f"{callback_info} has sent unexpected event {event}", extra=extra_params(user_id=user.id)
                )
        except Exception as e:
            self.logger.error("New event: logger error", exc_info=e)

        return await handler(event, data)
