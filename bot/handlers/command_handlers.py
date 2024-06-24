from datetime import datetime

from aiogram import Bot, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.handlers.subscription_handlers import send_subscription_expire_notify, send_subscription_end_notify
from bot.keyboards.subscription_keyboards import InlineSubscriptionContinueKeyboard
from bot.main import bot, cache_resources_file_id_store, user_db, bot_db, adv_db, subscription
from bot.keyboards import *
from bot.keyboards.main_menu_keyboards import InlineBotMenuKeyboard
from bot.states.states import States
from bot.handlers.routers import commands_router
from bot.utils.admin_group import send_event, EventTypes, success_event
from bot.exceptions.exceptions import *
from bot.utils.send_instructions import send_instructions
from bot.utils.check_subscription import check_subscription
from bot.middlewaries.subscription_middleware import CheckSubscriptionMiddleware
from database.models.adv_model import EmptyAdvTable, AdvSchema, AdvSchemaWithoutId

from logs.config import logger, adv_logger, extra_params

from database.models.user_model import UserSchema, UserStatusValues
from subscription.subscription import UserHasAlreadyStartedTrial


@commands_router.message(CommandStart())
async def start_command_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        await user_db.get_user(user_id)

        if message.text == "/start from_adv":
            adv_logger.info(
                f"user {user_id}, @{message.from_user.username}: tapped to adv again",
                extra=extra_params(user_id=user_id)
            )
            try:
                current_adv = await adv_db.get_last_adv()
                current_adv.total_count += 1
                await adv_db.add_adv(current_adv)
            except EmptyAdvTable:
                await adv_db.add_adv(AdvSchemaWithoutId.model_validate({"total_count": 1}))
            except Exception as e:
                logger.error(
                    e.__str__(),
                    extra=extra_params(user_id=user_id)
                )


    except UserNotFound:
        if message.text == "/start from_adv":
            adv_logger.info(
                f"user {user_id}, {message.from_user.username}: came here from adv",
                extra=extra_params(user_id=user_id)
            )
            try:
                current_adv = await adv_db.get_last_adv()
                current_adv.total_count += 1
                current_adv.total_unique_count += 1
                await adv_db.add_adv(current_adv)
            except EmptyAdvTable:
                await adv_db.add_adv(AdvSchemaWithoutId.model_validate({"total_count": 1, "total_unique_count": 1}))
            except Exception as e:
                logger.error(
                    e.__str__(),
                    extra=extra_params(user_id=user_id)
                )

        logger.info(f"user {user_id} not found in db, creating new instance...")

        await send_event(message.from_user, EventTypes.NEW_USER)
        await user_db.add_user(UserSchema(
            user_id=user_id, username=message.from_user.username, registered_at=datetime.utcnow(),
            status=UserStatusValues.NEW, locale="default", subscribed_until=None)
        )

        await _start_trial(message, state)

    user_bots = await bot_db.get_bots(user_id)
    await send_instructions(bot, user_bots[0].bot_id if user_bots else None, user_id, cache_resources_file_id_store)

    user_status = (await user_db.get_user(user_id)).status

    if user_status == UserStatusValues.SUBSCRIPTION_ENDED:  # TODO do not send it from States.WAITING_PAYMENT_APPROVE
        await message.answer(
            MessageTexts.SUBSCRIBE_END_NOTIFY.value,
            reply_markup=InlineSubscriptionContinueKeyboard.get_keyboard(bot_id=None)
        )
        return await state.set_state(States.SUBSCRIBE_ENDED)

    if not user_bots:
        await state.set_state(States.WAITING_FOR_TOKEN)
    else:
        bot_id = user_bots[0].bot_id
        user_bot = Bot(user_bots[0].token)
        user_bot_data = await user_bot.get_me()
        await message.answer(
            MessageTexts.BOT_MENU_MESSAGE.value.format(user_bot_data.username),
            reply_markup=await InlineBotMenuKeyboard.get_keyboard(user_bots[0].bot_id)
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


async def _start_trial(message: Message, state: FSMContext):
    admin_message = await send_event(message.from_user, EventTypes.STARTED_TRIAL)

    user_id = message.from_user.id
    # logger.info(f"starting trial subscription for user with id ({user_id} until date {subscribe_until}")
    # TODO move logger into to subscription module
    logger.info(
        f"starting trial subscription for user with id ({user_id} until date ТУТ нужно выполнить TODO"
    )

    try:
        subscribed_until = await subscription.start_trial(user_id)
    except UserHasAlreadyStartedTrial:
        # TODO выставлять счет на оплату если триал уже был но пользователь все равно как то сюда попал
        return await message.answer("Вы уже оформляли пробную подписку")

    logger.info(f"adding scheduled subscription notifies for user {user_id}")
    await subscription.add_notifications(
        user_id,
        on_expiring_notification=send_subscription_expire_notify,
        on_end_notification=send_subscription_end_notify,
        subscribed_until=subscribed_until,
    )

    await state.set_state(States.WAITING_FOR_TOKEN)

    await message.answer(
        MessageTexts.FREE_TRIAL_MESSAGE.value,
        reply_markup=ReplyKeyboardRemove()
    )
    await success_event(message.from_user, admin_message, EventTypes.STARTED_TRIAL)
