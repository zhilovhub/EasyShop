from datetime import timedelta, datetime

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.utils.formatting import Text, Bold, Italic
from aiogram.types import CallbackQuery, FSInputFile, User, Message
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from bot.main import subscription, bot, dp, cache_resources_file_id_store, SENT_SUBSCRIPTION_NOTIFICATIONS
from bot.utils import MessageTexts
from bot.states import States
from bot.handlers.routers import subscribe_router
from bot.utils.custom_bot_api import stop_custom_bot
from bot.utils.send_instructions import send_instructions
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard, ReplyBackBotMenuKeyboard
from bot.keyboards.subscription_keyboards import InlineSubscriptionContinueKeyboard, InlineAdminRefundKeyboard

from common_utils.env_config import RESOURCES_PATH, SBP_URL, ADMINS
from common_utils.keyboards.keyboards import InlineBotMenuKeyboard
from common_utils.broadcasting.broadcasting import send_event, EventTypes, success_event

from database.config import user_db, bot_db
from database.models.user_model import UserSchema, UserStatusValues

from logs.config import logger, extra_params


@subscribe_router.callback_query(lambda query: InlineSubscriptionContinueKeyboard.callback_validator(query.data))
async def continue_subscription_callback(query: CallbackQuery, state: FSMContext):
    callback_data = InlineSubscriptionContinueKeyboard.Callback.model_validate_json(query.data)

    state_data = await state.get_data()

    if callback_data.bot_id is not None:
        await state.set_data({"bot_id": callback_data.bot_id})

    photo_name, instruction = subscription.get_subscribe_instructions()
    await query.message.answer_photo(
        photo=FSInputFile(RESOURCES_PATH.format(photo_name)),
        caption=instruction,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Перейти на страницу оплаты", url=SBP_URL)
            ]
        ]))
    await query.message.answer(
        f"По возникновению каких-либо вопросов пишите @maxzim398",
        reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
    )
    await state.set_state(States.WAITING_PAYMENT_PAY)
    await state.set_data(state_data)


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
    await bot.send_message(
        actual_user.id,
        text,
        reply_markup=InlineSubscriptionContinueKeyboard.get_keyboard(bot_id=user_bot_id)
    )


@subscribe_router.message(States.WAITING_PAYMENT_PAY)
async def waiting_payment_pay_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_status = (await user_db.get_user(user_id)).status
    state_data = await state.get_data()

    if message.text == ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
        if user_status == UserStatusValues.SUBSCRIPTION_ENDED:
            await state.set_state(States.SUBSCRIBE_ENDED)
            await message.answer(
                MessageTexts.SUBSCRIBE_END_NOTIFY.value,
                reply_markup=InlineSubscriptionContinueKeyboard.get_keyboard(bot_id=None)
            )  # TODO change to keyboard markup
        elif state_data and "bot_id" in state_data:
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
            custom_bot = await bot_db.get_bot(state_data['bot_id'])

            await message.answer(
                "Возвращаемся в главное меню...",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id)
            )
        else:
            await state.set_state(States.WAITING_FOR_TOKEN)
            await send_instructions(bot, None, user_id, cache_resources_file_id_store)
            await message.answer("Ваш список ботов пуст, используйте инструкцию выше 👆")
        return
    elif message.content_type not in (ContentType.PHOTO, ContentType.DOCUMENT):
        return await message.answer(
            "Необходимо прислать боту чек в виде скрина или пдф файла",
            reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
        )
    elif not message.caption:
        return await message.answer(
            "В подписи к файлу или фото укажите Ваши контактные данные и отправьте чек повторно",
            reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
        )
    sent_message_ids = []
    for admin in ADMINS:
        try:
            msg: Message = await message.send_copy(admin)
            sent_msg = await bot.send_message(
                admin,
                f"💳 Оплата подписки от пользователя <b>"
                f"{'@' + message.from_user.username if message.from_user.username else message.from_user.full_name}"
                f"</b>",
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
                ])
            )
            sent_message_ids.append((admin, sent_msg.message_id))
        except Exception as e:
            logger.warning("error while notify admin", exc_info=e)

    json_data = SENT_SUBSCRIPTION_NOTIFICATIONS.get_data()
    json_data[str(message.from_user.id)] = sent_message_ids
    SENT_SUBSCRIPTION_NOTIFICATIONS.update_data(json_data)

    await message.reply(
        "Ваши данные отправлены на модерацию, ожидайте изменения статуса оплаты",
        reply_markup=ReplyBackBotMenuKeyboard.get_keyboard() if user_status in (
            UserStatusValues.SUBSCRIBED, UserStatusValues.TRIAL) else ReplyKeyboardRemove()
    )
    await state.set_state(States.WAITING_PAYMENT_APPROVE)
    await state.set_data(state_data)


@subscribe_router.message(States.WAITING_PAYMENT_APPROVE)
async def waiting_payment_approve_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_status = (await user_db.get_user(user_id)).status

    if user_status in (UserStatusValues.SUBSCRIBED,
                       UserStatusValues.TRIAL) \
            and message.text == ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])
        if state_data and "bot_id" in state_data:
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)

            await message.answer(
                "Возвращаемся в главное меню (мы Вас оповестим, когда оплата пройдет модерацию)...",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id)
            )
        else:
            await state.set_state(States.WAITING_FOR_TOKEN)
            await send_instructions(bot, None, user_id, cache_resources_file_id_store)
            await message.answer("Ваш список ботов пуст, используйте инструкцию выше 👆")
    else:
        await message.answer("Ваши данные отправлены на модерацию, ожидайте изменения статуса оплаты")


@subscribe_router.message(States.SUBSCRIBE_ENDED)
async def subscribe_ended_handler(message: Message) -> None:
    await message.answer(
        MessageTexts.SUBSCRIBE_END_NOTIFY.value,
        reply_markup=InlineSubscriptionContinueKeyboard.get_keyboard(bot_id=None)
    )


@subscribe_router.callback_query(lambda q: q.data.startswith("approve_pay"))
async def approve_pay_callback(query: CallbackQuery):
    user_id = int(query.data.split(':')[-1])

    user_chat_to_approve = await bot.get_chat(user_id)
    user_to_approve = User(
        id=user_id, is_bot=False, first_name=user_chat_to_approve.first_name, username=user_chat_to_approve.username
    )
    admin_message = await send_event(user_to_approve, EventTypes.SUBSCRIBED)

    subscribed_until = await subscription.approve_payment(user_id)

    user = await user_db.get_user(user_id)

    logger.info(f"adding scheduled subscription notifies for user {user.id}")
    await subscription.add_notifications(
        user_id,
        on_expiring_notification=send_subscription_expire_notify,
        on_end_notification=send_subscription_end_notify,
        subscribed_until=subscribed_until,
    )

    user_bots = await bot_db.get_bots(user_id)
    user_state = FSMContext(storage=dp.storage, key=StorageKey(
        chat_id=user_id,
        user_id=user_id,
        bot_id=bot.id))

    bot_id = None

    if user_bots:
        bot_id = user_bots[0].bot_id
        custom_bot = Bot(user_bots[0].token)
        user_bot_data = await custom_bot.get_me()

        await bot.send_message(
            user_id,
            "Оплата подписки подтверждена ✅",
            reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
        )
        await bot.send_message(
            user_id,
            MessageTexts.BOT_MENU_MESSAGE.value.format(user_bot_data.username),
            reply_markup=await InlineBotMenuKeyboard.get_keyboard(user_bots[0].bot_id)
        )
        await user_state.set_state(States.BOT_MENU)
        await user_state.set_data({'bot_id': bot_id})
    else:
        await user_state.set_state(States.WAITING_FOR_TOKEN)
        await bot.send_message(user_id, "Оплата подписки подтверждена ✅")
        await send_instructions(bot, None, user_id, cache_resources_file_id_store)
        await bot.send_message(
            user_id,
            "Чтобы получить бота с магазином, воспользуйтесь инструкцией выше 👆",
            reply_markup=ReplyKeyboardRemove()
        )
    await query.answer("Оплата подтверждена", show_alert=True)

    payment_id = 0  # TODO payment generation
    PAYMENT_APPROVED_TEXT = Text("\n\n✅ Оплата подписки подтверждена.",
                                 "\n\n📆 Дата подтверждения: ",
                                 Bold(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"),
                                 "\n\n👤 От админа: ",
                                 Bold('@' + str(query.from_user.username)),
                                 "\n\n🆔 Номер платежа: ",
                                 Italic(str(payment_id)))

    current_text = Text.from_entities(query.message.text, query.message.entities)
    message_text = current_text + PAYMENT_APPROVED_TEXT

    json_data = SENT_SUBSCRIPTION_NOTIFICATIONS.get_data()
    if str(user_id) in json_data:
        message_ids = json_data[str(user_id)]
    else:
        logger.warning(f"bot_id = {bot_id} : cant find old notification message ids for subscription for user {user_id}",
                       extra_params(bot_id=bot_id, user_id=user_id))
        message_ids = [(query.from_user.id, query.message.message_id), ]

    text, entities = message_text.render()
    for admin_id, msg_id in message_ids:
        await bot.edit_message_text(chat_id=int(admin_id),
                                    message_id=int(msg_id),
                                    text=text,
                                    entities=entities,
                                    reply_markup=InlineAdminRefundKeyboard.get_keyboard(bot_id, payment_id))

    await success_event(user_to_approve, bot, admin_message, EventTypes.SUBSCRIBED)


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
        user_id, f"По возникновению каких-либо вопросов, пишите @maxzim398",
        reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
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
        reply_markup=InlineSubscriptionContinueKeyboard.get_keyboard(bot_id=user_bot_id)
    )
    user_state = FSMContext(storage=dp.storage, key=StorageKey(
        chat_id=actual_user.id,
        user_id=actual_user.id,
        bot_id=bot.id))
    await user_state.set_state(States.SUBSCRIBE_ENDED)
