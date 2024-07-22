from datetime import datetime

from aiogram import F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.main import bot, cache_resources_file_id_store, subscription
from bot.utils import MessageTexts
from bot.states.states import States
from bot.handlers.routers import commands_router
from bot.utils.send_instructions import send_instructions
from bot.utils.check_subscription import check_subscription
from bot.handlers.subscription_handlers import send_subscription_expire_notify, send_subscription_end_notify
from bot.keyboards.subscription_keyboards import InlineSubscriptionContinueKeyboard
from bot.middlewaries.subscription_middleware import CheckSubscriptionMiddleware

from common_utils.keyboards.keyboards import InlineBotMenuKeyboard
from common_utils.subscription.subscription import UserHasAlreadyStartedTrial
from common_utils.broadcasting.broadcasting import send_event, EventTypes, success_event

from database.config import user_db, adv_db, bot_db, user_role_db
from database.exceptions import *
from database.models.adv_model import EmptyAdvTable, AdvSchemaWithoutId
from database.models.user_model import UserSchema, UserStatusValues
from database.models.user_role_model import UserRoleSchema, UserRoleValues

from logs.config import logger, adv_logger, extra_params


async def _handle_admin_invite_link(message: Message, params: list[str]):
    link_hash = params[0].split('_', maxsplit=1)[-1]
    try:
        db_bot = await bot_db.get_bot_by_invite_link_hash(link_hash)

        new_role = UserRoleSchema(user_id=message.from_user.id,
                                  bot_id=db_bot.bot_id,
                                  role=UserRoleValues.ADMINISTRATOR)
        await user_role_db.add_user_role(new_role)

        custom_bot_data = await Bot(token=db_bot.token).get_me()

        await message.answer(f"✅ Теперь Вы администратор бота @{custom_bot_data.username}")

        await bot.send_message(db_bot.created_by, f"🔔 Добавлен новый Администратор ("
                                                  f"{'@' + message.from_user.username if message.from_user.username else message.from_user.full_name}"
                                                  f") для бота "
                                                  f"@{custom_bot_data.username}")
        db_bot.admin_invite_link_hash = None
        await bot_db.update_bot(db_bot)
    except BotNotFound:
        return await message.answer("🚫 Пригласительная ссылка не найдена.")


@commands_router.message(CommandStart())
async def start_command_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    params = message.text.strip().split()
    params.pop(0)  # remove /start from params
    try:
        await user_db.get_user(user_id)

        if params and params[0] == "/start from_adv":
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
        elif params and params[0].startswith("admin_"):
            user_bots = await user_role_db.get_user_bots(user_id)
            if user_bots:
                return await message.answer("🚫 Вы не можете быть одновременно и админом и владельцем бота.")
            else:
                res = await _handle_admin_invite_link(message, params)
                if res is not None:
                    return res

    except UserNotFound:
        if params and params[0] == "/start from_adv":
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

        if params and params[0].startswith("admin_"):
            res = await _handle_admin_invite_link(message, params)
            if res is not None:
                return res
        else:
            await _start_trial(message, state)

    # user_bots = await bot_db.get_bots(user_id)
    user_bots = await user_role_db.get_user_bots(user_id)
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
            reply_markup=await InlineBotMenuKeyboard.get_keyboard(user_bots[0].bot_id, message.from_user.id)
        )
        await state.set_state(States.BOT_MENU)
        await state.set_data({'bot_id': bot_id})


@commands_router.message(F.text == "/clear")
async def clear_command_handler(message: Message, state: FSMContext) -> None:
    """ONLY FOR DEBUG BOT"""
    await user_db.del_user(user_id=message.from_user.id)
    await CheckSubscriptionMiddleware().__call__(start_command_handler, message, state)  # noqa


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
        user = await subscription.start_trial(user_id)
    except UserHasAlreadyStartedTrial:
        # TODO выставлять счет на оплату если триал уже был но пользователь все равно как то сюда попал
        return await message.answer("Вы уже оформляли пробную подписку")

    logger.info(f"adding scheduled subscription notifies for user {user_id}")
    notification_job_ids = await subscription.add_notifications(
        user_id,
        on_expiring_notification=send_subscription_expire_notify,
        on_end_notification=send_subscription_end_notify,
        subscribed_until=user.subscribed_until,
    )
    user.subscription_job_ids = notification_job_ids  # + [finish_job_id]
    await user_db.update_user(user)

    await state.set_state(States.WAITING_FOR_TOKEN)

    await message.answer(
        MessageTexts.FREE_TRIAL_MESSAGE.value,
        reply_markup=ReplyKeyboardRemove()
    )
    await success_event(message.from_user, bot, admin_message, EventTypes.STARTED_TRIAL)
