import asyncio
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter

from common_utils.config import main_telegram_bot_settings
from common_utils.message_texts import MessageTexts
from common_utils.bot_settings_config import BOT_PROPERTIES
from common_utils.broadcasting.broadcasting import EventTypes, send_event

from logs.config import logger


async def notify_about_error(event: CallbackQuery | Message | ChatMemberUpdated, error_message: str):
    await Bot(main_telegram_bot_settings.TELEGRAM_TOKEN, default=BOT_PROPERTIES).send_message(
        event.from_user.id, MessageTexts.UNKNOWN_ERROR_MESSAGE.value
    )
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
            if "message is not modified" in str(ex):
                logger.debug(f"Message is not modified API error while handling event: {event}")
                if isinstance(event, CallbackQuery):
                    return await event.answer("Эта кнопка уже нажата.")
            logger.error("Telegram API error while handling event", exc_info=ex)
            await notify_about_error(event, str(ex))
        except Exception as ex:
            logger.error("Error while handling event", exc_info=ex)
            await notify_about_error(event, str(ex))
