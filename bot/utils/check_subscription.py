from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.main import subscription
from bot.keyboards.subscription_keyboards import InlineSubscriptionContinueKeyboard

from database.models.user_model import UserStatusValues, UnknownUserStatus

from logs.config import logger, extra_params


async def check_subscription(event: Message | CallbackQuery, state: FSMContext = None) -> None:
    """Checks user status and handles the event considering it"""

    user_id = event.from_user.id
    try:
        bot_id = (await state.get_data())["bot_id"]
    except (KeyError, AttributeError):
        logger.warning(
            f"check_sub_cmd: bot_id of user {user_id} not found, setting it to None",
            extra=extra_params(user_id=user_id)
        )
        bot_id = None

    user_status = await subscription.get_user_status(user_id)
    match user_status:
        case UserStatusValues.SUBSCRIPTION_ENDED:
            message_text = f"Твоя подписка закончилась, чтобы продлить её на месяц нажми на кнопку ниже."
            if isinstance(event, Message):
                await event.answer(
                    message_text,
                    reply_markup=InlineSubscriptionContinueKeyboard.get_keyboard(bot_id=bot_id)
                )
            else:
                await event.answer(
                    message_text,
                    show_alert=True
                )
        case UserStatusValues.TRIAL | UserStatusValues.SUBSCRIBED:
            message_text = await subscription.get_when_expires_text(
                user_id=user_id,
                is_trial=(user_status == UserStatusValues.TRIAL)
            )
            if isinstance(event, Message):
                await event.answer(
                    message_text,
                    reply_markup=InlineSubscriptionContinueKeyboard.get_keyboard(bot_id=bot_id)
                )
            else:
                await event.answer(
                    message_text,
                    show_alert=True
                )
        case _:  # Здесь не должно оказаться пользователя со статусом NEW, ведь мы сразу оформляем для них TRIAL
            raise UnknownUserStatus(
                user_status=user_status, user_id=user_id
            )
