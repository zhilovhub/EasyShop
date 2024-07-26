from datetime import datetime

from aiogram import F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove

from bot.main import bot, cache_resources_file_id_store, subscription, dp
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

from database.config import user_db, bot_db, user_role_db
from database.models.bot_model import BotNotFoundError
from database.models.user_model import UserSchema, UserStatusValues, UserNotFoundError
from database.models.user_role_model import UserRoleSchema, UserRoleValues, UserRoleNotFoundError

from logs.config import logger


async def _handle_admin_invite_link(message: Message, params: list[str], state: FSMContext):
    link_hash = params[0].split('_', maxsplit=1)[-1]
    try:
        db_bot = await bot_db.get_bot_by_invite_link_hash(link_hash)

        new_role = UserRoleSchema(user_id=message.from_user.id,
                                  bot_id=db_bot.bot_id,
                                  role=UserRoleValues.ADMINISTRATOR)
        await user_role_db.add_user_role(new_role)

        custom_bot_data = await Bot(token=db_bot.token).get_me()

        await message.answer(f"✅ Теперь Вы администратор бота @{custom_bot_data.username}")

        await bot.send_message(
            db_bot.created_by,
            f"🔔 Добавлен новый Администратор ("
            f"{'@' + message.from_user.username if message.from_user.username else message.from_user.full_name}"
            f") для бота "
            f"@{custom_bot_data.username}"
        )
        db_bot.admin_invite_link_hash = None
        await bot_db.update_bot(db_bot)

        await message.answer(
            MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_data.username),
            reply_markup=await InlineBotMenuKeyboard.get_keyboard(db_bot.bot_id, message.from_user.id)
        )
        await state.set_state(States.BOT_MENU)
        await state.set_data({'bot_id': db_bot.bot_id})

    except BotNotFoundError:
        return await message.answer("🚫 Пригласительная ссылка не найдена.")


async def _send_bot_menu(user_id: int, user_state: FSMContext, user_bots: list | None):
    user_status = (await user_db.get_user(user_id)).status

    if user_status == UserStatusValues.SUBSCRIPTION_ENDED:  # TODO do not send it from States.WAITING_PAYMENT_APPROVE
        await bot.send_message(
            user_id,
            MessageTexts.SUBSCRIBE_END_NOTIFY.value,
            reply_markup=InlineSubscriptionContinueKeyboard.get_keyboard(bot_id=None)
        )
        return await user_state.set_state(States.SUBSCRIBE_ENDED)

    if not user_bots:
        return
    else:
        bot_id = user_bots[0].bot_id
        user_bot = Bot(user_bots[0].token)
        user_bot_data = await user_bot.get_me()
        await bot.send_message(
            user_id,
            MessageTexts.BOT_MENU_MESSAGE.value.format(user_bot_data.username),
            reply_markup=await InlineBotMenuKeyboard.get_keyboard(user_bots[0].bot_id, user_id)
        )
        await user_state.set_state(States.BOT_MENU)
        await user_state.set_data({'bot_id': bot_id})


async def remove_bot_admin(user_id: int, user_state: FSMContext):
    user_bots = await user_role_db.get_user_bots(user_id)

    if not user_bots:
        await send_instructions(bot, user_bots[0].bot_id if user_bots else None, user_id, cache_resources_file_id_store)
        await user_state.set_state(States.WAITING_FOR_TOKEN)
        await user_state.set_data({'bot_id': -1})
    else:
        await _send_bot_menu(user_id, user_state, user_bots)


@commands_router.message(CommandStart(deep_link=True))
async def deep_link_start_command_handler(message: Message, state: FSMContext, command: CommandObject):
    user_id = message.from_user.id
    params = command.args.split()

    if params[0] == "restart":
        await clear_start_command_handler(message, state)

    try:
        await user_db.get_user(user_id)

        if params and params[0].startswith("admin_"):
            user_bots = await user_role_db.get_user_bots(user_id)
            if user_bots:
                return await message.answer("🚫 Вы не можете быть одновременно и админом и владельцем бота.")
            else:
                res = await _handle_admin_invite_link(message, params, state)
                if res is not None:
                    return res

    except UserNotFoundError:
        logger.info(f"user {user_id} not found in db, creating new instance...")

        await send_event(message.from_user, EventTypes.NEW_USER)
        await user_db.add_user(UserSchema(
            user_id=user_id, username=message.from_user.username, registered_at=datetime.utcnow(),
            status=UserStatusValues.NEW, locale="default", subscribed_until=None)
        )

        if params and params[0].startswith("admin_"):
            res = await _handle_admin_invite_link(message, params, state)
            if res is not None:
                return res


@commands_router.message(CommandStart())
async def clear_start_command_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        await user_db.get_user(user_id)
    except UserNotFoundError:
        logger.info(f"user {user_id} not found in db, creating new instance...")

        await send_event(message.from_user, EventTypes.NEW_USER)
        await user_db.add_user(UserSchema(
            user_id=user_id, username=message.from_user.username, registered_at=datetime.utcnow(),
            status=UserStatusValues.NEW, locale="default", subscribed_until=None)
        )
        await _start_trial(message, state)

    user_bots = await user_role_db.get_user_bots(user_id)
    if not user_bots:
        user_bots = await bot_db.get_bots(user_id)

    await send_instructions(bot, user_bots[0].bot_id if user_bots else None, user_id, cache_resources_file_id_store)

    if not user_bots:
        await state.set_state(States.WAITING_FOR_TOKEN)
    else:
        await _send_bot_menu(user_id, state, user_bots)


@commands_router.message(Command("rm_admin"), StateFilter(States.BOT_MENU))
async def rm_admin_command_handler(message: Message, state: FSMContext, command: CommandObject):
    state_data = await state.get_data()
    bot_id = state_data['bot_id']
    if command.args is None:
        return await message.answer("🚫 Необходимо указать айди администратора")
    try:
        user_id = int(command.args)
        user_role = await user_role_db.get_user_role(user_id, bot_id)
    except ValueError:
        return await message.answer("🚫 UID должен быть числом")
    except UserRoleNotFoundError:
        return await message.answer("🔍 Админ с таким UID не найден.")

    await user_role_db.del_user_role(user_role.user_id, user_role.bot_id)

    custom_bot_data = await Bot((await bot_db.get_bot(bot_id)).token).get_me()

    await message.answer(f"🔔 Пользователь больше не администратор ({user_id}) для бота "
                         f"@{custom_bot_data.username}")

    user_state = FSMContext(storage=dp.storage, key=StorageKey(
            chat_id=user_id,
            user_id=user_id,
            bot_id=bot.id,
        )
    )

    await bot.send_message(user_id, "Вы больше не администратор этого бота.", reply_markup=ReplyKeyboardRemove())

    await remove_bot_admin(user_id, user_state)


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
