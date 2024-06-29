from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.main import subscription
from bot.keyboards.subscription_keyboards import InlineSubscriptionContinueKeyboard

from database.models.user_model import UserStatusValues

from logs.config import logger


async def check_subscription(message: Message, state: FSMContext = None):
    # TODO https://tracker.yandex.ru/BOT-17 Учесть часовые пояса клиентов
    user_id = message.from_user.id
    try:
        bot_id = (await state.get_data())["bot_id"]
    except (KeyError, AttributeError):
        logger.warning(f"check_sub_cmd: bot_id of user {user_id} not found, setting it to None")
        bot_id = None
    kb = InlineSubscriptionContinueKeyboard.get_keyboard(bot_id=bot_id)

    user_status = await subscription.get_user_status(user_id)
    match user_status:
        case UserStatusValues.SUBSCRIPTION_ENDED:
            await message.answer(f"Твоя подписка закончилась, чтобы продлить её на месяц нажми на кнопку ниже.",
                                 reply_markup=kb)
        case UserStatusValues.TRIAL | UserStatusValues.SUBSCRIBED:
            await message.answer(
                await subscription.get_when_expires_text(user_id, is_trial=(user_status == UserStatusValues.TRIAL)),
                reply_markup=kb
            )
        case _:
            await message.answer("Произошла ошибка. Администраторы уже уведомлены")
            raise Exception("Как они сюда попали?")
