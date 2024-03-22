import os
import string
from random import sample
from datetime import datetime, timedelta

from typing import *

from aiogram import Router, Bot, BaseMiddleware
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, CallbackQuery, ContentType, User
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest
from aiogram.fsm.context import FSMContext, StorageKey
from aiogram.utils.token import TokenValidationError, validate_token

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError

from bot import config
from bot.main import bot, db_engine, dp, subscription
from bot.utils import JsonStore
from bot.config import logger
from bot.keyboards import *
from bot.states.states import States
from bot.utils.admin_group import send_event, success_event, EventTypes
from bot.filters.chat_type import ChatTypeFilter
from bot.exceptions.exceptions import *

from database.models.bot_model import BotSchemaWithoutId, BotDao
from database.models.user_model import UserSchema, UserDao, UserStatusValues
from database.models.order_model import OrderSchema, OrderNotFound, OrderStatusValues, OrderDao
from database.models.product_model import ProductWithoutId, ProductDao
from database.models.payment_model import PaymentDao

from magic_filter import F

import json

from subscription.subscription import UserHasAlreadyStartedTrial


class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
            self,
            handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery | Message,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        message, is_message = (event, True) if isinstance(event, Message) else (event.message, False)
        try:
            await user_db.get_user(user_id)
        except UserNotFound:
            logger.info(f"user {user_id} not found in db, creating new instance...")
            await send_event(event.from_user, EventTypes.NEW_USER)
            await user_db.add_user(UserSchema(
                user_id=user_id, registered_at=datetime.utcnow(), status=UserStatusValues.NEW, locale="default",
                subscribed_until=None)
            )
            await message.answer(MessageTexts.ABOUT_MESSAGE.value)

        if user_id not in config.ADMINS and \
                not (await subscription.is_user_subscribed(user_id)) and \
                message.text not in ("/start", "/check_subscription"):
            if is_message:
                await message.answer("Для того, чтобы пользоваться ботом, тебе нужна подписка")
            else:
                await event.answer("Для того, чтобы пользоваться ботом, тебе нужна подписка", show_alert=True)
            return await check_sub_cmd(message)

        return await handler(event, data)


router = Router(name="subscribe_router")
router.message.filter(ChatTypeFilter(chat_type='private'))
router.message.middleware(CheckSubscriptionMiddleware())
router.callback_query.middleware(CheckSubscriptionMiddleware())

all_router = Router(name="all_router")
all_router.message.filter(ChatTypeFilter(chat_type='private'))

product_db: ProductDao = db_engine.get_product_db()
order_db: OrderDao = db_engine.get_order_dao()
bot_db: BotDao = db_engine.get_bot_dao()
user_db: UserDao = db_engine.get_user_dao()
pay_db: PaymentDao = db_engine.get_payment_dao()

cache_resources_file_id_store = JsonStore(
    file_path=config.RESOURCES_PATH.format("cache.json"),
    json_store_name="RESOURCES_FILE_ID_STORE"
)


@all_router.message(F.text == "/clear")
async def debug_clear(message: Message, state: FSMContext) -> None:
    """ONLY FOR DEBUG BOT"""
    await user_db.del_user(user_id=message.from_user.id)
    await CheckSubscriptionMiddleware().__call__(start_command_handler, message, state)


async def send_subscription_expire_notify(user: UserSchema):
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


async def send_subscription_end_notify(user: UserSchema):  # TODO https://tracker.yandex.ru/BOT-29 очищать джобы в бд
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


@router.callback_query(lambda q: q.data.startswith("order_"))
async def handle_callback(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    data = query.data.split(":")
    bot_token = (await bot_db.get_bot(state_data['bot_id'])).token

    try:
        order = await order_db.get_order(data[1])
    except OrderNotFound:
        await query.answer("Ошибка при работе с заказом, возможно статус уже изменился.", show_alert=True)
        return await query.message.edit_reply_markup(None)

    match data[0]:
        case "order_pre_cancel":
            await query.message.edit_reply_markup(reply_markup=create_cancel_confirm_kb(
                data[1], int(data[2]), int(data[3])))
        case "order_back_to_order":
            await query.message.edit_reply_markup(reply_markup=create_change_order_status_kb(
                data[1], int(data[2]), int(data[3]), current_status=order.status))
        case "order_finish" | "order_cancel" | "order_process" | "order_backlog" | "order_waiting_payment":
            order.status = {
                "order_cancel": OrderStatusValues.CANCELLED,
                "order_finish": OrderStatusValues.FINISHED,
                "order_process": OrderStatusValues.PROCESSING,
                "order_backlog": OrderStatusValues.BACKLOG,
                "order_waiting_payment": OrderStatusValues.WAITING_PAYMENT
            }[data[0]]

            await order_db.update_order(order)

            products = [(await product_db.get_product(product_id), product_count)
                        for product_id, product_count in order.products.items()]
            await Bot(bot_token, parse_mode=ParseMode.HTML).edit_message_text(
                order.convert_to_notification_text(products=products),
                reply_markup=None if data[0] in ("order_finish", "order_cancel") else
                create_cancel_order_kb(order.id, int(data[2]), int(data[3])),
                chat_id=data[3],
                message_id=int(data[2]))

            username = query.message.text[query.message.text.find("пользователя"):].split()[1].strip("\n")

            await query.message.edit_text(
                text=order.convert_to_notification_text(
                    products=products,
                    username=username,
                    is_admin=True
                ), reply_markup=None if data[0] in ("order_finish", "order_cancel") else
                create_change_order_status_kb(order.id, int(data[2]), int(data[3]), order.status))

            await Bot(bot_token, parse_mode=ParseMode.HTML).send_message(
                chat_id=data[3],
                text=f"Новый статус заказа <b>#{order.id}</b>\n<b>{order.translate_order_status()}</b>")





@all_router.callback_query(lambda q: q.data == "start_trial")
async def start_trial_callback(query: CallbackQuery, state: FSMContext):
    admin_message = await send_event(query.from_user, EventTypes.STARTED_TRIAL)
    await query.message.edit_text(MessageTexts.FREE_TRIAL_MESSAGE.value, reply_markup=None)
    user_id = query.from_user.id
    # logger.info(f"starting trial subscription for user with id ({user_id} until date {subscribe_until}")
    logger.info(
        f"starting trial subscription for user with id ({user_id} until date ТУТ нужно выполнить TODO")  # TODO move logger into to subscription module

    try:
        subscribed_until = await subscription.start_trial(query.from_user.id)
    except UserHasAlreadyStartedTrial:
        # TODO выставлять счет на оплату если триал уже был но пользователь все равно как то сюда попал
        return await query.answer("Вы уже оформляли пробную подписку", show_alert=True)

    logger.info(f"adding scheduled subscription notifies for user {user_id}")
    await subscription.add_notifications(
        user_id,
        on_expiring_notification=send_subscription_expire_notify,
        on_end_notification=send_subscription_end_notify,
        subscribed_until=subscribed_until,
    )

    await state.set_state(States.WAITING_FOR_TOKEN)

    await send_instructions(chat_id=query.from_user.id)
    await query.message.answer(
        "Ваша пробная подписка активирована!\n"
        "Чтобы получить бота с магазином, воспользуйтесь инструкцией выше 👆",
        reply_markup=ReplyKeyboardRemove()
    )
    await success_event(query.from_user, admin_message, EventTypes.STARTED_TRIAL)


@all_router.message(F.text == "/check_subscription")
async def check_sub_cmd(message: Message, state: FSMContext = None):
    # TODO https://tracker.yandex.ru/BOT-17 Учесть часовые пояса клиентов
    user_id = message.from_user.id
    try:
        bot_id = (await state.get_data())["bot_id"]
    except (KeyError, AttributeError):
        logger.warning(f"check_sub_cmd: bot_id of user {user_id} not found, setting it to None")
        bot_id = None
    kb = create_continue_subscription_kb(bot_id=bot_id)

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
        case UserStatusValues.NEW:
            await state.set_state(States.WAITING_FREE_TRIAL_APPROVE)
            await message.answer(MessageTexts.FREE_TRIAL_MESSAGE.value, reply_markup=free_trial_start_kb)


@all_router.callback_query(lambda q: q.data.startswith("continue_subscription"))
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


@all_router.message(States.WAITING_FREE_TRIAL_APPROVE)
async def waiting_free_trial_handler(message: Message) -> None:
    await message.answer(MessageTexts.FREE_TRIAL_MESSAGE.value, reply_markup=free_trial_start_kb)


@all_router.message(States.WAITING_PAYMENT_PAY)
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
            await send_instructions(chat_id=user_id)
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
            logger.warning("error while notify admin", exc_info=True)

    await message.reply(
        "Ваши данные отправлены на модерацию, ожидайте изменения статуса оплаты",
        reply_markup=get_back_keyboard() if user_status in (
            UserStatusValues.SUBSCRIBED, UserStatusValues.TRIAL) else ReplyKeyboardRemove()
    )
    await state.set_state(States.WAITING_PAYMENT_APPROVE)
    await state.set_data(state_data)


@all_router.message(States.WAITING_PAYMENT_APPROVE)
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
            await send_instructions(chat_id=user_id)
            await message.answer("Ваш список ботов пуст, используйте инструкцию выше 👆")
    else:
        await message.answer("Ваши данные отправлены на модерацию, ожидайте изменения статуса оплаты")


@all_router.message(States.SUBSCRIBE_ENDED)
async def subscribe_ended_handler(message: Message) -> None:
    await message.answer(
        MessageTexts.SUBSCRIBE_END_NOTIFY.value,
        reply_markup=create_continue_subscription_kb(bot_id=None)
    )


@all_router.callback_query(lambda q: q.data.startswith("approve_pay"))
async def approve_pay_callback(query: CallbackQuery, state: FSMContext):
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

    logger.info(f"adding scheduled subscription notifies for user {user.id}")
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
        await send_instructions(chat_id=user_id)
        await bot.send_message(
            user_id,
            "Чтобы получить бота с магазином, воспользуйтесь инструкцией выше 👆",
            reply_markup=ReplyKeyboardRemove()
        )
    await query.answer("Оплата подтверждена", show_alert=True)

    await success_event(user_to_approve, admin_message, EventTypes.SUBSCRIBED)


@all_router.callback_query(lambda q: q.data.startswith("cancel_pay"))
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


@router.message(States.WAITING_FOR_TOKEN)
async def waiting_for_the_token_handler(message: Message, state: FSMContext):
    user = await db_engine.get_user_dao().get_user(message.from_user.id)
    lang = user.locale
    token = message.text
    try:
        validate_token(token)

        found_bot = Bot(token)
        found_bot_data = await found_bot.get_me()
        bot_fullname, bot_username = found_bot_data.full_name, found_bot_data.username

        new_bot = BotSchemaWithoutId(bot_token=token,
                                     status="new",
                                     created_at=datetime.utcnow(),
                                     created_by=message.from_user.id,
                                     settings={"start_msg": MessageTexts.DEFAULT_START_MESSAGE.value,
                                               "default_msg":
                                                   f"Приветствую, этот бот создан с помощью @{(await bot.get_me()).username}",
                                               "web_app_button": MessageTexts.OPEN_WEB_APP_BUTTON_TEXT.value},
                                     locale=lang)

        bot_id = await bot_db.add_bot(new_bot)
        await start_custom_bot(bot_id)
    except TokenValidationError:
        return await message.answer(MessageTexts.INCORRECT_BOT_TOKEN_MESSAGE.value)
    except TelegramUnauthorizedError:
        return await message.answer(MessageTexts.BOT_WITH_TOKEN_NOT_FOUND_MESSAGE.value)
    except InstanceAlreadyExists:
        return await message.answer("Бот с таким токеном в системе уже найден.\n"
                                    "Введите другой токен или перейдите в список ботов и поищите Вашего бота там")
    except ClientConnectorError:
        logger.error("Cant connect to local api host (maybe service is offline)")
        return await message.answer("Сервис в данный момент недоступен, попробуйте еще раз позже")
    except Exception:
        logger.error(
            f"Unexpected error while adding new bot with token {token} from user {message.from_user.id}", exc_info=True
        )
        return await message.answer(":( Произошла ошибка при добавлении бота, попробуйте еще раз позже")
    user_bot = await bot_db.get_bot(bot_id)
    await message.answer(
        MessageTexts.BOT_INITIALIZING_MESSAGE.value.format(bot_fullname, bot_username),
        reply_markup=get_bot_menu_keyboard(bot_id, user_bot.status)
    )
    await state.set_state(States.BOT_MENU)
    await state.set_data({"bot_id": bot_id})


async def send_instructions(chat_id: int) -> None:
    file_ids = cache_resources_file_id_store.get_data()
    try:
        await bot.send_video(
            chat_id=chat_id,
            video=file_ids["botfather.mp4"],
            caption=MessageTexts.INSTRUCTION_MESSAGE.value
        )
    except (TelegramBadRequest, KeyError) as e:
        logger.info(f"error while sending instructions.... cache is empty, sending raw files {e}")
        video_message = await bot.send_video(
            chat_id=chat_id,
            video=FSInputFile(config.RESOURCES_PATH.format("botfather.mp4")),
            caption=MessageTexts.INSTRUCTION_MESSAGE.value
        )
        file_ids[f"botfather.mp4"] = video_message.video.file_id
        cache_resources_file_id_store.update_data(file_ids)
