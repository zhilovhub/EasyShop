from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.config import logger

from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter

from bot.utils.admin_group import send_event, EventTypes


async def notify_about_error(event: CallbackQuery | Message, error_message: str):
    await event.answer(":( Произошла неизвестная ошибка.")
    await send_event(event.from_user, EventTypes.NEW_USER, event.bot, err_msg=error_message)


class ErrorMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
            self,
            handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery | Message,
            data: Dict[str, Any]
    ) -> Any:
        try:
            result = await handler(event, data)
            return result
        except TelegramRetryAfter as ex:
            logger.warning(f"Flood control by API in telegram bot warning try in: {ex.retry_after} seconds")
            # TODO добавить задачу на переотправку запроса через ex.retry_after секунд
            # await scheduler.add_scheduled_job()
        except TelegramAPIError as ex:
            logger.error("Telegram API error while handling event", exc_info=True)
            await notify_about_error(event, str(ex))
        except Exception as ex:
            logger.error("Error while handling event", exc_info=True)
            await notify_about_error(event, str(ex))
