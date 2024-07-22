from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.config import user_role_db
from database.models.user_role_model import UserRoleValues, UserRoleNotFoundError


class CheckRoleMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
            self,
            handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery | Message,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        state: FSMContext = data["state"]
        state_data = await state.get_data()
        if not state_data or 'bot_id' not in state_data:
            if isinstance(event, CallbackQuery):
                await event.message.edit_reply_markup(reply_markup=None)
            return await event.answer("Ошибка состояния. Перезапустите бота.")
        try:
            user_role = await user_role_db.get_user_role(user_id, state_data['bot_id'])
            if user_role.role not in (UserRoleValues.ADMINISTRATOR, UserRoleValues.OWNER):
                raise UserRoleNotFoundError
        except UserRoleNotFoundError:
            if isinstance(event, CallbackQuery):
                await event.message.edit_reply_markup(reply_markup=None)
                return await event.answer("Вы больше не админ этого бота.", show_alert=True)
            else:
                return await event.answer("Вы больше не админ этого бота.")
        return await handler(event, data)
