from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from common_utils.keyboards.remove_keyboard import OurReplyKeyboardRemove

from database.config import user_role_db
from database.models.user_role_model import UserRoleValues, UserRoleNotFoundError


class CheckRoleMiddleware(BaseMiddleware):
    """Middleware that checks user state and user's role"""

    async def __call__(
        self,
        handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        state: FSMContext = data["state"]
        state_data = await state.get_data()

        empty_bot_state_data = {"bot_id": -1}

        if isinstance(event, Message) and state_data and "bot_id" in state_data and state_data["bot_id"] == -1:
            return await handler(event, data)

        if not state_data or "bot_id" not in state_data:
            await state.set_data(empty_bot_state_data)
            if isinstance(event, CallbackQuery):
                await event.message.edit_reply_markup(reply_markup=None)
            return await event.answer("Ошибка состояния. Напишите /start")

        try:
            user_role = await user_role_db.get_user_role(user_id, state_data["bot_id"])
            if user_role.role not in (UserRoleValues.ADMINISTRATOR, UserRoleValues.OWNER):
                raise UserRoleNotFoundError
        except UserRoleNotFoundError:
            await state.set_data(empty_bot_state_data)
            message_text = "Вы больше не админ этого бота. Напишите /start для возврата к своему или созданию нового"

            if isinstance(event, CallbackQuery):
                await event.message.edit_reply_markup(reply_markup=None)
                return await event.answer(message_text, show_alert=True)
            else:
                await state.set_data(empty_bot_state_data)
                return await event.answer(message_text, reply_markup=OurReplyKeyboardRemove())

        return await handler(event, data)
