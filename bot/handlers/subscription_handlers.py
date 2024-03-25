from datetime import timedelta, datetime

from aiogram import Bot
from aiogram.types import CallbackQuery, FSInputFile, User, Message
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from bot import config
from bot.main import subscription, bot, dp, cache_resources_file_id_store, user_db, bot_db
from bot.utils import MessageTexts
from bot.states import States
from bot.keyboards import get_bot_menu_keyboard, create_continue_subscription_kb, get_back_keyboard, free_trial_start_kb
from bot.handlers.routers import subscribe_router
from bot.utils.admin_group import EventTypes, send_event, success_event
from subscription.subscription import UserHasAlreadyStartedTrial
from database.models.user_model import UserSchema, UserStatusValues
from bot.utils.send_instructions import send_instructions
from bot.utils.custom_bot_api import stop_custom_bot


@subscribe_router.callback_query(lambda q: q.data == "start_trial")
async def start_trial_callback(query: CallbackQuery, state: FSMContext):
    admin_message = await send_event(query.from_user, EventTypes.STARTED_TRIAL)
    await query.message.edit_text(MessageTexts.FREE_TRIAL_MESSAGE.value, reply_markup=None)
    user_id = query.from_user.id
    # config.logger.info(f"starting trial subscription for user with id ({user_id} until date {subscribe_until}")
    # TODO move logger into to subscription module
    config.logger.info(
        f"starting trial subscription for user with id ({user_id} until date ТУТ нужно выполнить TODO"
    )

    try:
        subscribed_until = await subscription.start_trial(query.from_user.id)
    except UserHasAlreadyStartedTrial:
        # TODO выставлять счет на оплату если триал уже был но пользователь все равно как то сюда попал
        return await query.answer("Вы уже оформляли пробную подписку", show_alert=True)

    config.logger.info(f"adding scheduled subscription notifies for user {user_id}")
    await subscription.add_notifications(
        user_id,
        on_expiring_notification=send_subscription_expire_notify,
        on_end_notification=send_subscription_end_notify,
        subscribed_until=subscribed_until,
    )

    await state.set_state(States.WAITING_FOR_TOKEN)

    await send_instructions(bot, query.from_user.id, cache_resources_file_id_store)
    await query.message.answer(
        "Ваша пробная подписка активирована!\n"
        "Чтобы получить бота с магазином, воспользуйтесь инструкцией выше 👆",
        reply_markup=ReplyKeyboardRemove()
    )
    await success_event(query.from_user, admin_message, EventTypes.STARTED_TRIAL)


@subscribe_router.callback_query(lambda q: q.data.startswith("continue_subscription"))
async def continue_subscription_callback(query: CallbackQuery, state: FSMContext):
    await state.set_state(States.WAITING_PAYMENT_PAY)
    if query.data.split("_")[-1].isdigit():
        bot_id = int(query.data.split("_")[-1])
        await state.set_data({"bot_id": bot_id})

    photo_name, instruction = subscription.get_subscribe_instructions()
    await query.message.answer_photo(
        photo=FSInputFile(config.RESOURCES_PATH.format(photo_name)),
        caption=instruction,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Перейти на страницу оплаты", url=config.SBP_URL)
            ]
        ]))
    await query.message.answer(f"По возникновению каких-либо вопросов, пиши @someone", reply_markup=get_back_keyboard())


async def send_subscription_expire_notify(user: UserSchema) -> None:
    actual_user = await user_db.get_user(user.id)

    if datetime.now() > actual_user.subscribed_until:
        return None

    if (actual_user.subscribed_until - datetime.now()).days > 4:
        return None

    text = MessageTexts.SUBSCRIPTION_EXPIRE_NOTIFY.value
    text = text.replace("{expire_date}", actual_user.subscribed_until.strftime("%d.%m.%Y %H:%M"))
    text = text.replace("{expire_days}", str((actual_user.subscribed_until - datetime.now()).days))

    user_bots = await bot_db.get_bots(actual_user.id)
    if user_bots:
        user_bot_id = user_bots[0].bot_id
    else:
        user_bot_id = None
    await bot.send_message(actual_user.id, text, reply_markup=create_continue_subscription_kb(bot_id=user_bot_id))


@subscribe_router.message(States.WAITING_FREE_TRIAL_APPROVE)
async def waiting_free_trial_handler(message: Message) -> None:
    await message.answer(MessageTexts.FREE_TRIAL_MESSAGE.value, reply_markup=free_trial_start_kb)


@subscribe_router.message(States.WAITING_PAYMENT_PAY)
async def waiting_payment_pay_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_status = (await user_db.get_user(user_id)).status
    state_data = await state.get_data()

    if message.text == "🔙 Назад":
        if user_status == UserStatusValues.SUBSCRIPTION_ENDED:
            await state.set_state(States.SUBSCRIBE_ENDED)
            await message.answer(
                MessageTexts.SUBSCRIBE_END_NOTIFY.value,
                reply_markup=create_continue_subscription_kb(bot_id=None)
            )  # TODO change to keyboard markup
        elif state_data and "bot_id" in state_data:
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
            user_bot = await bot_db.get_bot(state_data['bot_id'])
            await message.answer(
                "Возвращаемся в главное меню...",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"], user_bot.status)
            )
        else:
            await state.set_state(States.WAITING_FOR_TOKEN)
            await send_instructions(bot, user_id, cache_resources_file_id_store)
            await message.answer("Ваш список ботов пуст, используйте инструкцию выше 👆")
        return
    elif message.content_type not in (ContentType.PHOTO, ContentType.DOCUMENT):
        return await message.answer(
            "Необходимо прислать боту чек в виде скрина или пдф файла",
            reply_markup=get_back_keyboard()
        )
    elif not message.caption:
        return await message.answer(
            "В подписи к файлу или фото укажите Ваши контактные данные и отправьте чек повторно",
            reply_markup=get_back_keyboard()
        )
    for admin in config.ADMINS:
        try:
            msg: Message = await message.send_copy(admin)
            await bot.send_message(admin, f"💳 Оплата подписки от пользователя <b>"
                                          f"{'@' + message.from_user.username if message.from_user.username else message.from_user.full_name}</b>",
                                   reply_to_message_id=msg.message_id,
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [
                                           InlineKeyboardButton(text="Подтвердить оплату",
                                                                callback_data=f"approve_pay:{message.from_user.id}")
                                       ],
                                       [
                                           InlineKeyboardButton(text="Отклонить оплату",
                                                                callback_data=f"cancel_pay:{message.from_user.id}")
                                       ]
                                   ]))
        except:
            config.logger.warning("error while notify admin", exc_info=True)

    await message.reply(
        "Ваши данные отправлены на модерацию, ожидайте изменения статуса оплаты",
        reply_markup=get_back_keyboard() if user_status in (
            UserStatusValues.SUBSCRIBED, UserStatusValues.TRIAL) else ReplyKeyboardRemove()
    )
    await state.set_state(States.WAITING_PAYMENT_APPROVE)
    await state.set_data(state_data)


@subscribe_router.message(States.WAITING_PAYMENT_APPROVE)
async def waiting_payment_approve_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_status = (await user_db.get_user(user_id)).status

    if user_status in (UserStatusValues.SUBSCRIBED, UserStatusValues.TRIAL) and message.text == "🔙 Назад":
        state_data = await state.get_data()
        user_bot = await bot_db.get_bot(state_data['bot_id'])
        if state_data and "bot_id" in state_data:
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
            await message.answer(
                "Возвращаемся в главное меню (мы Вас оповестим, когда оплата пройдет модерацию)...",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"], user_bot.status)
            )
        else:
            await state.set_state(States.WAITING_FOR_TOKEN)
            await send_instructions(bot, user_id, cache_resources_file_id_store)
            await message.answer("Ваш список ботов пуст, используйте инструкцию выше 👆")
    else:
        await message.answer("Ваши данные отправлены на модерацию, ожидайте изменения статуса оплаты")


@subscribe_router.message(States.SUBSCRIBE_ENDED)
async def subscribe_ended_handler(message: Message) -> None:
    await message.answer(
        MessageTexts.SUBSCRIBE_END_NOTIFY.value,
        reply_markup=create_continue_subscription_kb(bot_id=None)
    )


@subscribe_router.callback_query(lambda q: q.data.startswith("approve_pay"))
async def approve_pay_callback(query: CallbackQuery):
    await query.message.edit_text(query.message.text + "\n\n<b>ПОДТВЕРЖДЕНО</b>", reply_markup=None)
    user_id = int(query.data.split(':')[-1])

    user_chat_to_approve = await bot.get_chat(user_id)
    user_to_approve = User(
        id=user_id, is_bot=False, first_name=user_chat_to_approve.first_name, username=user_chat_to_approve.username
    )
    admin_message = await send_event(user_to_approve, EventTypes.SUBSCRIBED)

    subscribed_until = await subscription.approve_payment(user_id)

    user = await user_db.get_user(user_id)
    await subscription.create_payment(user_id)

    config.logger.info(f"adding scheduled subscription notifies for user {user.id}")
    await subscription.add_notifications(
        user_id,
        on_expiring_notification=send_subscription_expire_notify,
        on_end_notification=send_subscription_end_notify,
        subscribed_until=subscribed_until,
    )

    await bot.send_message(user_id, "Оплата подписки подтверждена ✅")
    user_bots = await bot_db.get_bots(user_id)
    user_state = FSMContext(storage=dp.storage, key=StorageKey(
        chat_id=user_id,
        user_id=user_id,
        bot_id=bot.id))

    if user_bots:
        bot_id = user_bots[0].bot_id
        user_bot = Bot(user_bots[0].token)
        user_bot_data = await user_bot.get_me()
        await bot.send_message(user_id, MessageTexts.BOT_SELECTED_MESSAGE.value.format(user_bot_data.username),
                               reply_markup=get_bot_menu_keyboard(bot_id=bot_id, bot_status=user_bots[0].status))
        await user_state.set_state(States.BOT_MENU)
        await user_state.set_data({'bot_id': bot_id})
    else:
        await user_state.set_state(States.WAITING_FOR_TOKEN)
        await send_instructions(bot, user_id, cache_resources_file_id_store)
        await bot.send_message(
            user_id,
            "Чтобы получить бота с магазином, воспользуйтесь инструкцией выше 👆",
            reply_markup=ReplyKeyboardRemove()
        )
    await query.answer("Оплата подтверждена", show_alert=True)

    await success_event(user_to_approve, admin_message, EventTypes.SUBSCRIBED)


@subscribe_router.callback_query(lambda q: q.data.startswith("cancel_pay"))
async def cancel_pay_callback(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    user_id = int(query.data.split(':')[-1])
    await query.message.edit_text(query.message.text + "\n\n<b>ОТКЛОНЕНО</b>", reply_markup=None)

    user_state = FSMContext(storage=dp.storage, key=StorageKey(
        chat_id=user_id,
        user_id=user_id,
        bot_id=bot.id))

    await user_state.set_state(States.WAITING_PAYMENT_PAY)
    await user_state.set_data(state_data)

    await bot.send_message(user_id, "Оплата не была принята, перепроверьте корректность отправленных данный (чека) "
                                    "и отправьте его еще раз")
    await bot.send_message(
        user_id, f"По возникновению каких-либо вопросов, пишите @someone", reply_markup=get_back_keyboard()
    )

    await query.answer("Оплата отклонена", show_alert=True)


async def send_subscription_end_notify(user: UserSchema) -> None:
    # TODO https://tracker.yandex.ru/BOT-29 очищать джобы в бд
    actual_user = await user_db.get_user(user.id)

    # check if there any new subscription (in this case we should not end it)
    if datetime.now() + timedelta(minutes=5) < actual_user.subscribed_until:
        return None

    actual_user.status = UserStatusValues.SUBSCRIPTION_ENDED
    await user_db.update_user(actual_user)

    user_bots = await bot_db.get_bots(actual_user.id)
    if user_bots:
        user_bot_id = user_bots[0].bot_id
        await stop_custom_bot(user_bot_id)
    else:
        user_bot_id = None
    await bot.send_message(
        actual_user.id,
        MessageTexts.SUBSCRIBE_END_NOTIFY.value,
        reply_markup=create_continue_subscription_kb(bot_id=user_bot_id)
    )
    user_state = FSMContext(storage=dp.storage, key=StorageKey(
        chat_id=actual_user.id,
        user_id=actual_user.id,
        bot_id=bot.id))
    await user_state.set_state(States.SUBSCRIBE_ENDED)
