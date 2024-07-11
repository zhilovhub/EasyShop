from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.handlers.routers import empty_router
from bot.handlers.command_handlers import start_command_handler

from logs.config import logger, extra_params


@empty_router.message()
async def empty_state_message_handler(message: Message, state: FSMContext):
    logger.warning(
        f"user_id={message.from_user.id}: user got to empty_state_message_handler",
        extra=extra_params(user_id=message.from_user.id)
    )
    await start_command_handler(message, state)
