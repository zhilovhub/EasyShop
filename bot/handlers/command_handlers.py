from datetime import datetime

from aiogram import Bot, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.main import bot, cache_resources_file_id_store, user_db, bot_db
from bot.config import logger
from bot.keyboards import *
from bot.states.states import States
from bot.handlers.routers import commands_router
from bot.utils.admin_group import send_event, EventTypes
from bot.exceptions.exceptions import *
from bot.utils.send_instructions import send_instructions
from bot.utils.check_subscription import check_subscription
from bot.middlewaries.subscription_middleware import CheckSubscriptionMiddleware

from database.models.user_model import UserSchema, UserStatusValues


@commands_router.message(CommandStart())
async def start_command_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        await user_db.get_user(user_id)
    except UserNotFound:
        logger.info(f"user {user_id} not found in db, creating new instance...")
        await send_event(message.from_user, EventTypes.NEW_USER)
        await user_db.add_user(UserSchema(
            user_id=user_id, registered_at=datetime.utcnow(), status=UserStatusValues.NEW, locale="default",
            subscribed_until=None)
        )

    await send_instructions(bot, user_id, cache_resources_file_id_store)

    user_status = (await user_db.get_user(user_id)).status

    if user_status == UserStatusValues.SUBSCRIPTION_ENDED:  # TODO do not send it from States.WAITING_PAYMENT_APPROVE
        await message.answer(
            MessageTexts.SUBSCRIBE_END_NOTIFY.value,
            reply_markup=create_continue_subscription_kb(bot_id=None)
        )
        return await state.set_state(States.SUBSCRIBE_ENDED)

    user_bots = await bot_db.get_bots(user_id)
    if not user_bots:
        if user_status == UserStatusValues.NEW:
            await message.answer(MessageTexts.FREE_TRIAL_MESSAGE.value, reply_markup=free_trial_start_kb)
            await state.set_state(States.WAITING_FREE_TRIAL_APPROVE)
        else:
            await state.set_state(States.WAITING_FOR_TOKEN)
    else:
        bot_id = user_bots[0].bot_id
        user_bot = Bot(user_bots[0].token)
        user_bot_data = await user_bot.get_me()
        await message.answer(
            MessageTexts.BOT_SELECTED_MESSAGE.value.format(user_bot_data.username),
            reply_markup=get_bot_menu_keyboard(bot_id=bot_id, bot_status=user_bots[0].status)
        )
        await state.set_state(States.BOT_MENU)
        await state.set_data({'bot_id': bot_id})


@commands_router.message(F.text == "/clear")
async def clear_command_handler(message: Message, state: FSMContext) -> None:
    """ONLY FOR DEBUG BOT"""
    await user_db.del_user(user_id=message.from_user.id)
    await CheckSubscriptionMiddleware().__call__(start_command_handler, message, state)


@commands_router.message(F.text == "/check_subscription")
async def check_subscription_command_handler(message: Message, state: FSMContext):
    await check_subscription(message, state)
