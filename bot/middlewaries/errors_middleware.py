import asyncio
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter

from bot.main import bot
from bot.utils.admin_group import send_event, EventTypes

from logs.config import logger


async def notify_about_error(event: CallbackQuery | Message | ChatMemberUpdated, error_message: str):
    await bot.send_message(event.from_user.id, ":( Произошла неизвестная ошибка")
    await send_event(event.from_user, EventTypes.UNKNOWN_ERROR, event.bot, err_msg=error_message)


class ErrorMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
            self,
            handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery | Message | ChatMemberUpdated,
            data: Dict[str, Any]
    ) -> Any:
        try:
            result = await handler(event, data)
            return result
        except TelegramRetryAfter as ex:
            logger.warning(f"Flood control by API in telegram bot warning try in: {ex.retry_after} seconds")
            await asyncio.sleep(ex.retry_after + 1000)
            return await handler(event, data)
        except TelegramAPIError as ex:
            logger.error("Telegram API error while handling event", exc_info=True)
            await notify_about_error(event, str(ex))
        except Exception as ex:
            logger.error("Error while handling event", exc_info=True)
            await notify_about_error(event, str(ex))
