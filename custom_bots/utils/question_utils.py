import time

from aiogram.types import CallbackQuery

from logs.config import custom_bot_logger, extra_params


async def is_able_to_ask(query: CallbackQuery, state_data: dict, user_id: int, order_id: str) -> bool:
    if "last_question_time" in state_data and time.time() - state_data["last_question_time"] < 1 * 60 * 60:
        custom_bot_logger.info(
            f"user_id={user_id}: too early for asking question about order_id={order_id}",
            extra=extra_params(user_id=user_id, order_id=order_id),
        )
        await query.answer(
            "Вы уже задавали вопрос недавно, пожалуйста, попробуйте позже " "(между вопросами должен пройти час)",
            show_alert=True,
        )
        return False

    return True
