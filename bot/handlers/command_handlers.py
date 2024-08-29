from datetime import datetime

from aiogram import F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from bot.main import bot, subscription, dp, START_MESSAGE_ANALYTICS
from bot.start_message_analytics.start_message_analytics_cache import (
    StartMessageAnalyticSchema,
    UserStartMessageActionSchema,
)
from bot.utils import MessageTexts
from bot.states.states import States
from bot.handlers.routers import commands_router
from bot.utils.send_instructions import greetings_message
from bot.utils.check_subscription import check_subscription
from bot.handlers.subscription_handlers import send_subscription_expire_notify, send_subscription_end_notify
from bot.keyboards.subscription_keyboards import InlineSubscriptionContinueKeyboard
from bot.keyboards.start_keyboards import (
    InstructionKeyboard,
    ShortDescriptionKeyboard,
    RefShortDescriptionKeyboard,
    RefFullDescriptionKeyboard,
    RefLinkKeyboard,
    CALLBACK_TO_STRING_NAME,
)
from bot.middlewaries.subscription_middleware import CheckSubscriptionMiddleware

from common_utils.ref_utils import send_ref_user_info
from common_utils.tests_utils import messages_collector
from common_utils.subscription import config
from common_utils.keyboards.keyboards import InlineBotMenuKeyboard
from common_utils.keyboards.remove_keyboard import OurReplyKeyboardRemove
from common_utils.subscription.subscription import UserHasAlreadyStartedTrial
from common_utils.exceptions.bot_exceptions import UnknownDeepLinkArgument
from common_utils.broadcasting.broadcasting import send_event, EventTypes

from database.config import user_db, bot_db, user_role_db, referral_invite_db
from database.models.bot_model import BotNotFoundError
from database.models.user_model import UserSchema, UserStatusValues, UserNotFoundError
from database.models.user_role_model import UserRoleSchema, UserRoleValues, UserRoleNotFoundError
from database.models.referral_invite_model import ReferralInviteSchemaWithoutId

from logs.config import logger, extra_params


@commands_router.callback_query(lambda query: ShortDescriptionKeyboard.callback_validator(query.data))
async def short_description_handler(query: CallbackQuery):
    callback_data = ShortDescriptionKeyboard.Callback.model_validate_json(query.data)

    chat_id = query.from_user.id
    from_chat_id = -1002218211760

    _update_analytics(callback_data.a, chat_id, query.from_user.username)
    match callback_data.a:
        case callback_data.ActionEnum.START_USING:
            await query.message.delete()
            await bot.forward_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=8)
            await query.message.answer(
                **MessageTexts.generate_menu_start_text(), reply_markup=InstructionKeyboard.get_keyboard()
            )

        case callback_data.ActionEnum.REF_DESCRIPTION:
            await query.message.delete()
            await bot.forward_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=18)
            await query.message.answer(
                **MessageTexts.generate_menu_start_text(), reply_markup=RefShortDescriptionKeyboard.get_keyboard()
            )


@commands_router.callback_query(lambda query: InstructionKeyboard.callback_validator(query.data))
async def instructions_handler(query: CallbackQuery):
    callback_data = InstructionKeyboard.Callback.model_validate_json(query.data)

    chat_id = query.from_user.id
    from_chat_id = -1002218211760

    _update_analytics(callback_data.a, chat_id, query.from_user.username)
    match callback_data.a:
        case callback_data.ActionEnum.BACK:
            await query.message.delete()
            await bot.forward_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=6)
            await query.message.answer(
                **MessageTexts.generate_menu_start_text(), reply_markup=ShortDescriptionKeyboard.get_keyboard()
            )


@commands_router.callback_query(lambda query: RefShortDescriptionKeyboard.callback_validator(query.data))
async def ref_short_description_handler(query: CallbackQuery):
    callback_data = RefShortDescriptionKeyboard.Callback.model_validate_json(query.data)

    chat_id = query.from_user.id
    from_chat_id = -1002218211760

    _update_analytics(callback_data.a, chat_id, query.from_user.username)
    match callback_data.a:
        case callback_data.ActionEnum.REWARDS:
            await query.message.delete()
            await bot.forward_messages(chat_id=chat_id, from_chat_id=from_chat_id, message_ids=[10, 11, 12, 13])
            await query.message.answer(
                **MessageTexts.generate_menu_start_text(), reply_markup=RefFullDescriptionKeyboard.get_keyboard()
            )
        case callback_data.ActionEnum.BACK:
            await query.message.delete()
            await bot.forward_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=6)
            await query.message.answer(
                **MessageTexts.generate_menu_start_text(), reply_markup=ShortDescriptionKeyboard.get_keyboard()
            )


@commands_router.callback_query(lambda query: RefFullDescriptionKeyboard.callback_validator(query.data))
async def ref_full_description_handler(query: CallbackQuery):
    callback_data = RefFullDescriptionKeyboard.Callback.model_validate_json(query.data)

    chat_id = query.from_user.id
    from_chat_id = -1002218211760

    _update_analytics(callback_data.a, chat_id, query.from_user.username)
    match callback_data.a:
        case callback_data.ActionEnum.CONTINUE:
            await send_ref_user_info(query.message, query.from_user.id, bot)
        case callback_data.ActionEnum.BACK:
            await query.message.delete()
            await bot.forward_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=18)
            await query.message.answer(
                **MessageTexts.generate_menu_start_text(), reply_markup=RefShortDescriptionKeyboard.get_keyboard()
            )
        case callback_data.ActionEnum.MENU:
            await query.message.delete()
            await bot.forward_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=6)
            await query.message.answer(
                **MessageTexts.generate_menu_start_text(), reply_markup=ShortDescriptionKeyboard.get_keyboard()
            )


@commands_router.callback_query(lambda query: RefLinkKeyboard.callback_validator(query.data))
async def ref_link_handler(query: CallbackQuery):
    callback_data = RefLinkKeyboard.Callback.model_validate_json(query.data)

    chat_id = query.from_user.id
    from_chat_id = -1002218211760

    _update_analytics(callback_data.a, chat_id, query.from_user.username)
    match callback_data.a:
        case callback_data.ActionEnum.BACK:
            await query.message.delete()
            await bot.forward_messages(chat_id=chat_id, from_chat_id=from_chat_id, message_ids=[10, 11, 12, 13])
            await query.message.answer(
                **MessageTexts.generate_menu_start_text(), reply_markup=RefFullDescriptionKeyboard.get_keyboard()
            )
        case callback_data.ActionEnum.MENU:
            await query.message.delete()
            await bot.forward_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=6)
            await query.message.answer(
                **MessageTexts.generate_menu_start_text(), reply_markup=ShortDescriptionKeyboard.get_keyboard()
            )


async def _handle_admin_invite_link(message: Message, state: FSMContext, deep_link_params: list[str]):
    """Проверяет пригласительную ссылку и добавляет пользователя в администраторы"""

    link_hash = deep_link_params[0].split("_", maxsplit=1)[-1]
    try:
        db_bot = await bot_db.get_bot_by_invite_link_hash(link_hash)

        new_role = UserRoleSchema(user_id=message.from_user.id, bot_id=db_bot.bot_id, role=UserRoleValues.ADMINISTRATOR)
        await user_role_db.add_user_role(new_role)

        custom_bot_data = await Bot(token=db_bot.token).get_me()

        await message.answer(f"✅ Теперь Вы администратор бота @{custom_bot_data.username}")

        await bot.send_message(
            db_bot.created_by,
            f"🔔 Добавлен новый Администратор ("
            f"{'@' + message.from_user.username if message.from_user.username else message.from_user.full_name}"
            f") для бота "
            f"@{custom_bot_data.username}",
        )
        db_bot.admin_invite_link_hash = None
        await bot_db.update_bot(db_bot)

        await message.answer(
            MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_data.username),
            reply_markup=await InlineBotMenuKeyboard.get_keyboard(db_bot.bot_id, message.from_user.id),
        )
        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": db_bot.bot_id})

    except BotNotFoundError:
        return await message.answer("🚫 Пригласительная ссылка не найдена.")


@messages_collector()
async def _send_bot_menu(user_id: int, state: FSMContext, user_bots: list | None):
    user_status = (await user_db.get_user(user_id)).status

    if user_status == UserStatusValues.SUBSCRIPTION_ENDED:  # TODO do not send it from States.WAITING_PAYMENT_APPROVE
        yield await bot.send_message(
            user_id,
            MessageTexts.SUBSCRIBE_END_NOTIFY.value,
            reply_markup=InlineSubscriptionContinueKeyboard.get_keyboard(bot_id=None),
        )
        yield await bot.send_message(
            user_id, MessageTexts.SUBSCRIBE_END_NOTIFY_PART_2.value, reply_markup=OurReplyKeyboardRemove()
        )
        await state.set_state(States.SUBSCRIBE_ENDED)
        await state.set_data({"bot_id": -1})
        return

    if not user_bots:
        await state.set_state(States.WAITING_FOR_TOKEN)  # Просто ожидаем токен, так как ботов у человека нет
        await state.set_data({"bot_id": -1})
        return
    else:
        bot_id = user_bots[0].bot_id
        user_bot = Bot(user_bots[0].token)
        user_bot_data = await user_bot.get_me()
        yield await bot.send_message(
            user_id,
            MessageTexts.BOT_MENU_MESSAGE.value.format(user_bot_data.username),
            reply_markup=await InlineBotMenuKeyboard.get_keyboard(user_bots[0].bot_id, user_id),
        )
        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})


async def remove_bot_admin(user_id: int, message: Message, user_state: FSMContext):
    user_bots = await user_role_db.get_user_bots(user_id)

    if not user_bots:
        await greetings_message(bot, user_bots[0].bot_id if user_bots else None, message)
        await user_state.set_state(States.WAITING_FOR_TOKEN)
        await user_state.set_data({"bot_id": -1})
    else:
        await _send_bot_menu(user_id, user_state, user_bots)


@commands_router.message(CommandStart(deep_link=True))
async def deep_link_start_command_handler(message: Message, state: FSMContext, command: CommandObject):
    """
    Проверяет команду /start с параметрами: restart, admin, kostya_seller, ref

    :raises UnknownDeepLinkArgument:
    """
    user_id = message.from_user.id
    deep_link_params = command.args.split()

    if deep_link_params[0] == "restart":
        await start_command_handler(message, state)
    elif deep_link_params[0].startswith("admin_"):
        await _check_if_new_user(message, state)  # Проверяем, новый ли пользователь

        user_bots = await user_role_db.get_user_bots(user_id)
        if user_bots:
            await message.answer("🚫 Вы не можете быть одновременно и админом и владельцем бота.")
        else:
            await _handle_admin_invite_link(message, state, deep_link_params)
    elif deep_link_params[0] == "kostya_seller":
        await _check_if_new_user(
            message, state, config.BIG_TRIAL_DURATION_IN_DAYS
        )  # Проверяем, новый ли пользователь и задаем пробный период на 30 дней
    elif deep_link_params[0].startswith("ref_"):
        await _check_if_new_user(
            message,
            state,
            is_ref=True,
            came_from=int(deep_link_params[0].split("_")[1]),
        )  # Проверяем, новый ли пользователь
    else:
        raise UnknownDeepLinkArgument(arg=deep_link_params)


@messages_collector()
async def _check_if_new_user(
    message: Message,
    state: FSMContext,
    trial_duration: int = config.TRIAL_DURATION_IN_DAYS,
    is_ref: bool = False,
    came_from: int = None,
):
    user_id = message.from_user.id
    is_first_message = False

    try:  # Проверка, есть ли такой пользователь (если нет то это новый пользователь)
        await user_db.get_user(user_id)
    except UserNotFoundError:
        logger.info(f"user {user_id} not found in db, creating new instance...")
        await send_event(message.from_user, EventTypes.NEW_USER)
        await user_db.add_user(
            UserSchema(
                user_id=user_id,
                username=message.from_user.username,
                registered_at=datetime.utcnow(),
                status=UserStatusValues.NEW,
                subscribed_until=None,
            )
        )
        is_first_message = True

        if is_ref:
            logger.info(f"adding user {user_id} to referral system...")
            await referral_invite_db.add_invite(ReferralInviteSchemaWithoutId(user_id=user_id, came_from=came_from))

        await _start_trial(message, state, trial_duration)  # Задаём новому пользователю пробный период (статус TRIAL)

    user_bots = await user_role_db.get_user_bots(user_id)

    # Отправляем инструкцию. Если у человека есть бот, к инструкции добавится клавиатурное (не inline) меню бота.
    yield await greetings_message(
        bot, user_bots[0].bot_id if user_bots else None, message, is_first_message=is_first_message
    )

    yield await _send_bot_menu(user_id, state, user_bots)  # Присылаем inline меню бота, так как у человека бот есть


@commands_router.message(CommandStart())
@messages_collector(expected_types=[Message, FSMContext])
async def start_command_handler(message: Message, state: FSMContext):
    """
    1. Встречает пользователя, проверяет, есть ли он в базе данных. Если нет, то создаёт, так как видимо пользователь
    новый.
    2. ВСЕГДА присылает инструкцию
    3. Проверяет, есть ли у пользователя боты, которыми он может управлять.
        3.1 Если есть боты, то переводит в состояние BOT_MENU и присылает все клавиатуры для главного меню бота.
        3.2 Если нет ботов, то переводит в состояние WAITING_FOR_TOKEN
    """

    yield await _check_if_new_user(message, state)  # Проверяем, новый ли пользователь


@commands_router.message(Command("rm_admin"), StateFilter(States.BOT_MENU))
async def rm_admin_command_handler(message: Message, state: FSMContext, command: CommandObject):
    """Обрабатывает удаление администратора, ожидая в параметрах UID администратора"""

    state_data = await state.get_data()
    bot_id = state_data["bot_id"]
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

    await message.answer(
        f"🔔 Пользователь больше не администратор ({user_id}) для бота " f"@{custom_bot_data.username}"
    )

    user_state = FSMContext(
        storage=dp.storage,
        key=StorageKey(
            chat_id=user_id,
            user_id=user_id,
            bot_id=bot.id,
        ),
    )

    await bot.send_message(user_id, "Вы больше не администратор этого бота.", reply_markup=OurReplyKeyboardRemove())

    await remove_bot_admin(user_id, message, user_state)


@commands_router.message(F.text == "/clear")
async def clear_command_handler(message: Message, state: FSMContext) -> None:
    """
    ONLY FOR DEBUG BOT: сносит пользователя из БД.
    Но не удаляет его состояние, поэтому нужно не забыть после этой команды вызвать /start
    """
    await user_db.del_user(user_id=message.from_user.id)
    await CheckSubscriptionMiddleware().__call__(start_command_handler, message, state)  # noqa


@commands_router.message(F.text == "/check_subscription")
async def check_subscription_command_handler(message: Message, state: FSMContext):
    """Проверяет статус подписки"""
    await check_subscription(message, state)


async def _start_trial(message: Message, state: FSMContext, trial_duration: int):
    """Оформляет пробный период пользователю"""
    notifications_before_days = config.NOTIFICATIONS_BEFORE_DAYS

    match trial_duration:
        case config.TRIAL_DURATION_IN_DAYS:
            await send_event(message.from_user, EventTypes.STARTED_TRIAL_TRY)
        case config.BIG_TRIAL_DURATION_IN_DAYS:
            await send_event(message.from_user, EventTypes.STARTED_BIG_TRIAL_TRY)
            notifications_before_days = [7, 2]

    user_id = message.from_user.id

    logger.info(f"starting trial subscription for user with id ({user_id} until date")

    try:
        user = await subscription.start_trial(user_id, trial_duration)
    except UserHasAlreadyStartedTrial:
        return await message.answer("Вы уже оформляли пробную подписку")

    logger.info(f"adding scheduled subscription notifies for user {user_id}")
    notification_job_ids = await subscription.add_notifications(
        user_id,
        on_expiring_notification=send_subscription_expire_notify,
        on_end_notification=send_subscription_end_notify,
        subscribed_until=user.subscribed_until,
        notifications_before_days=notifications_before_days,
    )
    user.subscription_job_ids = notification_job_ids
    await user_db.update_user(user)

    await state.set_state(States.WAITING_FOR_TOKEN)

    await send_event(message.from_user, EventTypes.STARTED_TRIAL_SUCCESS)


def _update_analytics(action, user_id: int, username: str) -> None:
    """
    Method to add new user action to json analytics

    See bot/start_message_analytics/start_message_analytics_cache.py
    See bot/keyboards/start_keyboards.py
    """
    logger.info(f"user_id={user_id}: new start_message action: {action}", extra=extra_params(user_id=user_id))

    current_data = StartMessageAnalyticSchema(**START_MESSAGE_ANALYTICS.get_data())

    action_value_raw = CALLBACK_TO_STRING_NAME[action]
    action_value = action_value_raw if isinstance(action_value_raw, str) else " ".join(action_value_raw)
    current_data.actions.append(
        UserStartMessageActionSchema(
            user_id=user_id,
            username=username,
            action=action_value,
            date=datetime.now(tz=None).strftime("%m_%d_%Y, %H:%M:%S"),
        )
    )
    current_data_dict = current_data.model_dump()
    current_data_dict[action_value] += 1

    START_MESSAGE_ANALYTICS.update_data(StartMessageAnalyticSchema(**current_data_dict).model_dump())
