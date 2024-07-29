from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.main import MAINTENANCE

from logs.config import logger


class MaintenanceMiddleware(BaseMiddleware):
    """Middleware that doesn't allow user communicate to the bot during Maintenance"""

    async def __call__(
            self,
            handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery | Message,
            data: Dict[str, Any]
    ) -> Any:
        json_data = MAINTENANCE.get_data()
        if not json_data:
            json_data = {
                "maintenance":
                    {
                        "maintenance_status": False,
                        "maintenance_reason": None
                    }
            }
            logger.info(f"maintenance json data is empty, setting new default data {json_data}")
            MAINTENANCE.update_data(json_data)

        if json_data['maintenance']['maintenance_status']:
            if not json_data['maintenance']['maintenance_reason']:
                json_data['maintenance']['maintenance_reason'] = "🛠 Бот находится в режиме обслуживания"  # noqa
                MAINTENANCE.update_data(json_data)
            if isinstance(event, Message):
                await event.answer(json_data['maintenance']['maintenance_reason'])
            else:
                await event.message.answer(json_data['maintenance']['maintenance_reason'])
        else:
            return await handler(event, data)
