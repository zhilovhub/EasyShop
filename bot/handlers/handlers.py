import os
import string
from random import sample
from datetime import datetime, timedelta

from typing import *

from aiogram import Router, Bot, BaseMiddleware
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, CallbackQuery, InputMediaPhoto, ContentType
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest
from aiogram.fsm.context import FSMContext, StorageKey
from aiogram.utils.token import TokenValidationError, validate_token

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError

from bot import config
from bot.main import bot, db_engine, scheduler, dp
from bot.utils import JsonStore
from bot.config import logger
from bot.keyboards import *
from bot.states.states import States
from bot.filters.chat_type import ChatTypeFilter
from bot.exceptions.exceptions import *

from database.models.bot_model import BotSchemaWithoutId, BotDao
from database.models.user_model import UserSchema, UserDao
from database.models.order_model import OrderSchema, OrderNotFound, OrderStatusValues, OrderDao
from database.models.product_model import ProductWithoutId, ProductDao
from database.models.payment_model import PaymentSchemaWithoutId, PaymentDao

from magic_filter import F

import json


class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
            self,
            handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery | Message,
            data: Dict[str, Any]
    ) -> Any:
        message = event if isinstance(event, Message) else event.message
        try:
            user = await user_db.get_user(event.from_user.id)
        except UserNotFound:
            logger.info(f"user {event.from_user.id} not found in db, creating new instance...")
            await user_db.add_user(UserSchema(
                user_id=event.from_user.id, registered_at=datetime.utcnow(), status="new", locale="default",
                subscribed_until=None)
            )
            await message.answer(MessageTexts.ABOUT_MESSAGE.value)
            user = await user_db.get_user(event.from_user.id)

        if user.id not in config.ADMINS and \
                user.status not in ("subscribed", "trial") and \
                message.text not in ("/start", "/check_subscription"):
            await event.answer(
                "Для того, чтобы пользоваться ботом, тебе нужна подписка")  # TODO move it into check_sub_cmd
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
async def sd(message: Message, state: FSMContext):  # TODO remove after payment tests
    await user_db.del_user(user_id=message.from_user.id)
    await start_command_handler(message, state)


async def start_custom_bot(bot_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"http://{config.LOCAL_API_SERVER_HOST}:{config.LOCAL_API_SERVER_PORT}/start_bot/{bot_id}") as response:
            if response.status != 200:
                raise LocalAPIException(f"API returned {response.status} status code "
                                        f"with text {await response.text()}")


async def stop_custom_bot(bot_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"http://{config.LOCAL_API_SERVER_HOST}:{config.LOCAL_API_SERVER_PORT}/stop_bot/{bot_id}") as response:
            if response.status != 200:
                raise LocalAPIException(f"API returned {response.status} status code "
                                        f"with text {await response.text()}")


async def send_new_order_notify(order: OrderSchema, user_id: int):
    order_user_data = await bot.get_chat(order.from_user)
    products = [(await product_db.get_product(product_id), product_count)
                for product_id, product_count in order.products.items()]

    await bot.send_message(user_id, f"Так будет выглядеть у тебя уведомление о новом заказе 👇")
    await bot.send_message(
        user_id, order.convert_to_notification_text(
            products,
            "@" + order_user_data.username if order_user_data.username else order_user_data.full_name,
            True
        )
    )


async def send_order_change_status_notify(order: OrderSchema):
    user_bot = await bot_db.get_bot(order.bot_id)
    text = f"Новый статус заказ <b>#{order.id}</b>\n<b>{order.status}</b>"
    await bot.send_message(user_bot.created_by, text)
    await bot.send_message(order.from_user, text)


async def send_subscription_expire_notify(user: UserSchema):
    actual_user = await user_db.get_user(user.id)

    if datetime.now() > actual_user.subscribed_until:
        return None

    if (actual_user.subscribed_until - datetime.now()).seconds > 60:  # TODO change it to 7 days
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
    if datetime.now() + timedelta(seconds=5) < actual_user.subscribed_until:  # TODO change it to 5 minutes
        return None

    actual_user.status = "subscription_ended"
    await user_db.update_user(actual_user)

    user_bots = await bot_db.get_bots(actual_user.id)
    if user_bots:
        user_bot_id = user_bots[0].bot_id
    else:
        user_bot_id = None
    await bot.send_message(
        actual_user.id,
        MessageTexts.SUBSCRIBE_END_NOTIFY.value,
        reply_markup=create_continue_subscription_kb(bot_id=user_bot_id)
    )  # TODO change to keyboard markup
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


@router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    try:
        data = json.loads(event.web_app_data.data)
        logger.info(f"receive web app data: {data}")

        data["from_user"] = user_id
        data["status"] = "backlog"
        data["count"] = 0

        order = OrderSchema(**data)

        logger.info(f"order with id #{order.id} created")
    except Exception:
        logger.warning("error while creating order", exc_info=True)
        return await event.answer("Произошла ошибка при создании заказа, попробуйте еще раз.")

    try:
        await send_new_order_notify(order, user_id)
    except Exception as ex:
        logger.warning("error while sending test order notification", exc_info=True)


@all_router.message(CommandStart())
async def start_command_handler(message: Message, state: FSMContext = None):  # TODO rempve = None after payment tests
    user_id = message.from_user.id
    try:
        await user_db.get_user(user_id)
    except UserNotFound:
        logger.info(f"user {user_id} not found in db, creating new instance...")

        await user_db.add_user(UserSchema(
            user_id=user_id, registered_at=datetime.utcnow(), status="new", locale="default",
            subscribed_until=None)
        )

    await send_instructions(message)

    user_bots = await bot_db.get_bots(user_id)
    if not user_bots:
        user_status = (await user_db.get_user(user_id)).status
        if user_status == "new":
            await message.answer(MessageTexts.FREE_TRIAL_MESSAGE.value, reply_markup=free_trial_start_kb)
            await state.set_state(States.WAITING_FREE_TRIAL_APPROVE)
        elif user_status == "subscription_ended":
            await message.answer(
                MessageTexts.SUBSCRIBE_END_NOTIFY.value,
                reply_markup=create_continue_subscription_kb(bot_id=None)
            )  # TODO change to keyboard markup
            await state.set_state(States.SUBSCRIBE_ENDED)
        else:
            await state.set_state(States.WAITING_FOR_TOKEN)
    else:
        bot_id = user_bots[0].bot_id
        user_bot = Bot(user_bots[0].token)
        user_bot_data = await user_bot.get_me()
        await message.answer(
            MessageTexts.BOT_SELECTED_MESSAGE.value.format(user_bot_data.username),
            reply_markup=get_bot_menu_keyboard(bot_id=bot_id)
        )
        await state.set_state(States.BOT_MENU)
        await state.set_data({'bot_id': bot_id})


@all_router.callback_query(lambda q: q.data == "start_trial")
async def start_trial_callback(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text(MessageTexts.FREE_TRIAL_MESSAGE.value, reply_markup=None)

    subscribe_until = datetime.now() + timedelta(seconds=60)  # TODO change it to 7 days
    logger.info(f"starting trial subscription for user with id ({query.from_user.id} until date {subscribe_until}")
    user = await user_db.get_user(query.from_user.id)
    if user.status != "new":
        # TODO выставлять счет на оплату если триал уже был но пользователь все равно как то сюда попал
        return await query.answer("Вы уже оформляли пробную подписку", show_alert=True)
    user.status = "trial"
    user.subscribed_until = subscribe_until

    logger.info(f"adding scheduled subscription notifies for user {user.id}")
    await scheduler.add_scheduled_job(func=send_subscription_expire_notify,
                                      run_date=subscribe_until - timedelta(seconds=40),  # TODO change it to 3 days
                                      args=[user])
    await scheduler.add_scheduled_job(func=send_subscription_expire_notify,
                                      run_date=subscribe_until - timedelta(seconds=20),  # TODO change it to 1 day
                                      args=[user])
    await scheduler.add_scheduled_job(func=send_subscription_end_notify,
                                      run_date=subscribe_until,
                                      args=[user])

    await user_db.update_user(user)
    await state.set_state(States.WAITING_FOR_TOKEN)

    await send_instructions(query.message)
    await query.message.answer(
        "Ваша пробная подписка активирована!\n"
        "Чтобы получить бота с магазином, воспользуйся инструкцией выше 👆",
        reply_markup=ReplyKeyboardRemove()
    )


@all_router.message(F.text == "/check_subscription")
async def check_sub_cmd(message: Message, state: FSMContext = None):
    # TODO https://tracker.yandex.ru/BOT-17 Учесть часовые пояса клиентов
    user = await user_db.get_user(message.from_user.id)
    try:
        bot_id = (await state.get_data())["bot_id"]
    except (KeyError, AttributeError):
        logger.warning(f"check_sub_cmd: bot_id of user {user.id} not found, setting it to None")
        bot_id = None
    kb = create_continue_subscription_kb(bot_id=bot_id)

    if user.status == "subscription_ended":
        await message.answer(f"Твоя подписка закончилась, чтобы продлить её на месяц нажми на кнопку ниже.",
                             reply_markup=kb)
    elif user.status == "trial":
        await message.answer(f"Твоя бесплатная подписка истекает "
                             f"<b>{user.subscribed_until.strftime('%d.%m.%Y %H:%M')}</b> "
                             f"(через <b>{(user.subscribed_until - datetime.now()).days}</b> дней)."
                             f"\nХочешь продлить прямо сейчас?", reply_markup=kb)
    elif user.status == "subscribed":
        await message.answer(f"Твоя подписка истекает "
                             f"<b>{user.subscribed_until.strftime('%d.%m.%Y %H:%M')}</b> "
                             f"(через <b>{(user.subscribed_until - datetime.now()).days}</b> дней)."
                             f"\nХочешь продлить прямо сейчас?", reply_markup=kb)
    elif user.status == "new":
        await state.set_state(States.WAITING_FREE_TRIAL_APPROVE)
        await message.answer(MessageTexts.FREE_TRIAL_MESSAGE.value, reply_markup=free_trial_start_kb)


@all_router.callback_query(lambda q: q.data.startswith("continue_subscription"))
async def continue_subscription_callback(query: CallbackQuery, state: FSMContext):
    await state.set_state(States.WAITING_PAYMENT_PAY)
    if query.data.split("_")[-1].isdigit():
        bot_id = int(query.data.split("_")[-1])
        await state.set_data({"bot_id": bot_id})

    await query.message.answer_photo(FSInputFile(f"{config.RESOURCES_PATH.replace('{}', 'sbp_qr.png')}"),
                                     f"• Стоимость подписки: <b>{config.SUBSCRIPTION_PRICE}₽</b>\n\n"
                                     f"• Оплачивайте подписку удобным способом, "
                                     f"через qr код. Либо на карту сбербанка по номеру телефона: "
                                     f"<code>{config.SBP_NUM}</code>\n\n"
                                     f"• После оплаты пришлите боту чек (скрин или пдфку) с подтверждением оплаты.\n\n"
                                     f"• В подписи к фото <b>напишите Ваши контакты для связи</b> с "
                                     f"Вами в случае возникновения вопросов по оплате.",
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
        if user_status == "subscription_ended":
            await state.set_state(States.SUBSCRIBE_ENDED)
            await message.answer(
                MessageTexts.SUBSCRIBE_END_NOTIFY.value,
                reply_markup=create_continue_subscription_kb(bot_id=None)
            )  # TODO change to keyboard markup
        elif state_data and "bot_id" in state_data:
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
            await message.answer(
                "Возвращаемся в главное меню...",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"])
            )
        else:
            await state.set_state(States.WAITING_FOR_TOKEN)
            await send_instructions(message)
            await message.answer("Твой список ботов пуст, используй инструкцию выше 👆")
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
        reply_markup=get_back_keyboard() if user_status in ("subscribed", "trial") else ReplyKeyboardRemove()
    )
    await state.set_state(States.WAITING_PAYMENT_APPROVE)
    await state.set_data(state_data)


@all_router.message(States.WAITING_PAYMENT_APPROVE)
async def waiting_payment_approve_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_status = (await user_db.get_user(user_id)).status

    if user_status in ("subscribed", "trial") and message.text == "🔙 Назад":
        state_data = await state.get_data()

        if state_data and "bot_id" in state_data:
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
            await message.answer(
                "Возвращаемся в главное меню (мы Вас оповестим, когда оплата пройдет модерацию)...",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"])
            )
        else:
            await state.set_state(States.WAITING_FOR_TOKEN)
            await send_instructions(message)
            await message.answer("Твой список ботов пуст, используй инструкцию выше 👆")
    else:
        await message.answer("Ваши данные отправлены на модерацию, ожидайте изменения статуса оплаты")


@all_router.message(States.SUBSCRIBE_ENDED)
async def subscribe_ended_handler(message: Message) -> None:
    await message.answer(
        MessageTexts.SUBSCRIBE_END_NOTIFY.value,
        reply_markup=create_continue_subscription_kb(bot_id=None)
    )  # TODO change to keyboard markup


@all_router.callback_query(lambda q: q.data.startswith("approve_pay"))
async def approve_pay_callback(query: CallbackQuery, state: FSMContext):
    user_id = int(query.data.split(':')[-1])
    user = await user_db.get_user(user_id)
    await query.message.edit_text(query.message.text + "\n\n<b>ПОДТВЕРЖДЕНО</b>", reply_markup=None)
    payment = PaymentSchemaWithoutId(from_user=user_id,
                                     amount=config.SUBSCRIPTION_PRICE,
                                     status="success",
                                     created_at=datetime.now(),
                                     last_update=datetime.now())
    await pay_db.add_payment(payment)
    user_state = FSMContext(storage=dp.storage, key=StorageKey(
        chat_id=user_id,
        user_id=user_id,
        bot_id=bot.id))
    if user.status == "subscription_ended":
        user.subscribed_until = datetime.now() + timedelta(seconds=60)  # TODO change it to 31 days
    else:
        user.subscribed_until = user.subscribed_until + timedelta(seconds=60)  # TODO change it to 31 days
    user.status = "subscribed"

    logger.info(f"adding scheduled subscription notifies for user {user.id}")
    await scheduler.add_scheduled_job(func=send_subscription_expire_notify,
                                      run_date=user.subscribed_until - timedelta(seconds=40),
                                      # TODO change it to 3 days
                                      args=[user])
    await scheduler.add_scheduled_job(func=send_subscription_expire_notify,
                                      run_date=user.subscribed_until - timedelta(seconds=20),  # TODO change it to 1 day
                                      args=[user])
    await scheduler.add_scheduled_job(func=send_subscription_end_notify,
                                      run_date=user.subscribed_until,
                                      args=[user])

    await user_db.update_user(user)

    await bot.send_message(user_id, "Оплата подписки подтверждена")
    user_bots = await bot_db.get_bots(user_id)

    if user_bots:
        bot_id = user_bots[0].bot_id
        user_bot = Bot(user_bots[0].token)
        user_bot_data = await user_bot.get_me()
        await bot.send_message(user_id, MessageTexts.BOT_SELECTED_MESSAGE.value.format(user_bot_data.username),
                               reply_markup=get_bot_menu_keyboard(bot_id=bot_id))
        await user_state.set_state(States.BOT_MENU)
        await user_state.set_data({'bot_id': bot_id})
    else:
        await user_state.set_state(States.WAITING_FOR_TOKEN)
        file_ids = cache_resources_file_id_store.get_data()

        try:
            await bot.send_media_group(user_id,
                                       media=[
                                           InputMediaPhoto(media=file_ids["botFather1.jpg"],
                                                           caption=MessageTexts.INSTRUCTION_MESSAGE.value),
                                           InputMediaPhoto(media=file_ids["botFather2.jpg"]),
                                           InputMediaPhoto(media=file_ids["botFather3.jpg"])
                                       ]
                                       )
        except (TelegramBadRequest, KeyError) as e:
            logger.info(f"error while sending instructions.... cache is empty, sending raw files {e}")
            media_group = await bot.send_media_group(user_id,
                                                     media=[
                                                         InputMediaPhoto(media=FSInputFile(
                                                             config.RESOURCES_PATH.format("botFather1.jpg")),
                                                             caption=MessageTexts.INSTRUCTION_MESSAGE.value),
                                                         InputMediaPhoto(media=FSInputFile(
                                                             config.RESOURCES_PATH.format("botFather2.jpg"))),
                                                         InputMediaPhoto(media=FSInputFile(
                                                             config.RESOURCES_PATH.format("botFather3.jpg"))),
                                                     ]
                                                     )
            for ind, message in enumerate(media_group, start=1):
                file_ids[f"botFather{ind}.jpg"] = message.photo[0].file_id
            cache_resources_file_id_store.update_data(file_ids)
    await query.answer("Оплата подтверждена.", show_alert=True)


@all_router.callback_query(lambda q: q.data.startswith("cancel_pay"))  # TODO обработать это
async def cancel_pay_callback(query: CallbackQuery, state: FSMContext):
    user_id = int(query.data.split(':')[-1])
    await query.message.edit_text(query.message.text + "\n\n<b>ОТКЛОНЕНО</b>", reply_markup=None)

    user_state = FSMContext(storage=dp.storage, key=StorageKey(
        chat_id=user_id,
        user_id=user_id,
        bot_id=bot.id))
    await user_state.set_state(States.WAITING_PAYMENT_PAY)

    await bot.send_message(user_id, "Оплата не была принята, перепроверьте корректность отправленных данный (чека) "
                                    "и отправьте его еще раз.")
    await bot.send_message(
        user_id, f"По возникновению каких-либо вопросов, пиши @someone", reply_markup=get_back_keyboard()
    )

    await query.answer("Оплата отклонена.", show_alert=True)


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
                                                   f"Привет, этот бот создан с помощью @{(await bot.get_me()).username}",
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
                                    "Введи другой токен или перейди в список ботов и поищи своего бота там")
    except ClientConnectorError:
        logger.error("Cant connect to local api host (maybe service is offline)")
        return await message.answer("Сервис в данный момент недоступен, попробуй еще раз позже.")
    except Exception:
        logger.error(
            f"Unexpected error while adding new bot with token {token} from user {message.from_user.id}", exc_info=True
        )
        return await message.answer(":( Произошла ошибка при добавлении бота, попробуй еще раз позже.")
    await message.answer(
        MessageTexts.BOT_INITIALIZING_MESSAGE.value.format(bot_fullname, bot_username),
        reply_markup=get_bot_menu_keyboard(bot_id)
    )
    await state.set_state(States.BOT_MENU)
    await state.set_data({"bot_id": bot_id})


@router.message(States.BOT_MENU, F.photo)
async def bot_menu_photo_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    photo_file_id = message.photo[-1].file_id

    if message.caption is None:
        return await message.answer("Чтобы добавить товар, прикрепи его картинку и отправь сообщение в виде:"
                                    "\n\nНазвание\nЦена в рублях")

    params = message.caption.strip().split('\n')
    filename = "".join(sample(string.ascii_letters + string.digits, k=5)) + ".jpg"

    if len(params) != 2:
        return await message.answer("Чтобы добавить товар, прикрепи его картинку и отправь сообщение в виде:"
                                    "\n\nНазвание\nЦена в рублях")
    if params[-1].isdigit():
        price = int(params[-1])
    else:
        return await message.answer("Цена должна быть <b>целым числом</b>")

    await bot.download(photo_file_id, destination=f"{os.getenv('FILES_PATH')}{filename}")

    new_product = ProductWithoutId(bot_id=state_data['bot_id'],
                                   name=params[0],
                                   description="",
                                   price=price,
                                   count=0,
                                   picture=filename)
    await db_engine.get_product_db().add_product(new_product)
    await message.answer("Товар добавлен. Можно добавить ещё")


@router.message(States.BOT_MENU)
async def bot_menu_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    match message.text:
        case "Стартовое сообщение":
            await message.answer("Пришли текст, который должен присылаться пользователям, "
                                 "когда они твоему боту отправляют /start", reply_markup=get_back_keyboard())
            await state.set_state(States.EDITING_START_MESSAGE)
            await state.set_data(state_data)
        case "Сообщение затычка":
            await message.answer("Пришли текст, который должен присылаться пользователям "
                                 "на их любые обычные сообщения", reply_markup=get_back_keyboard())
            await state.set_state(States.EDITING_DEFAULT_MESSAGE)
            await state.set_data(state_data)
        case "Магазин":
            pass  # should be pass, it's nice
        case "Список товаров":
            products = await db_engine.get_product_db().get_all_products(state_data["bot_id"])
            if not products:
                await message.answer("Список товаров твоего магазина пуст")
            else:
                await message.answer("Список товаров твоего магазина 👇\nЧтобы удалить товар, нажми на тег рядом с ним")
                for product in products:
                    await message.answer_photo(
                        photo=FSInputFile(os.getenv('FILES_PATH') + product.picture),
                        caption=f"<b>{product.name}</b>\n\n"
                                f"Цена: <b>{float(product.price)}₽</b>",
                        reply_markup=get_inline_delete_button(product.id))
        case "Добавить товар":
            await message.answer("Чтобы добавить товар, прикрепи его картинку и отправь сообщение в виде:"
                                 "\n\nНазвание\nЦена в рублях")
        case "Запустить бота":
            await start_custom_bot(state_data['bot_id'])
            await message.answer("Твой бот запущен ✅")
        case "Остановить бота":
            await stop_custom_bot(state_data['bot_id'])
            await message.answer("Твой бот приостановлен ❌")
        case "Удалить бота":
            await message.answer("Бот удалится вместе со всей базой продуктов безвозвратно.\n"
                                 "Напиши ПОДТВЕРДИТЬ для подтверждения удаления", reply_markup=get_back_keyboard())
            await state.set_state(States.DELETE_BOT)
            await state.set_data(state_data)
        case _:
            await message.answer(
                "Для навигации используй кнопки 👇",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"])
            )


@router.message(States.EDITING_START_MESSAGE)
async def editing_start_message_handler(message: Message, state: FSMContext):
    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"])
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            user_bot = await db_engine.get_bot_dao().get_bot(state_data["bot_id"])
            if user_bot.settings:
                user_bot.settings["start_msg"] = message_text
            else:
                user_bot.settings = {"start_msg": message_text}
            await db_engine.get_bot_dao().update_bot(user_bot)

            await message.answer(
                "Стартовое сообщение изменено!",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"])
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@router.message(States.EDITING_DEFAULT_MESSAGE)
async def editing_default_message_handler(message: Message, state: FSMContext):
    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"])
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            user_bot = await db_engine.get_bot_dao().get_bot(state_data["bot_id"])
            if user_bot.settings:
                user_bot.settings["default_msg"] = message_text
            else:
                user_bot.settings = {"default_msg": message_text}
            await db_engine.get_bot_dao().update_bot(user_bot)

            await message.answer(
                "Сообщение-затычка изменена!",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"])
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
    else:
        await message.answer("Сообщение-затычка должна содержать текст")


@router.message(States.DELETE_BOT)
async def delete_bot_handler(message: Message, state: FSMContext):
    message_text = message.text
    state_data = await state.get_data()
    if message_text == "ПОДТВЕРДИТЬ":
        logger.info(f"Disabling bot {state_data['bot_id']}, setting deleted status to db...")
        user_bot = await bot_db.get_bot(state_data["bot_id"])
        user_bot.status = "Deleted"
        await bot_db.del_bot(user_bot.bot_id)

        await message.answer(
            "Бот удален",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(MessageTexts.INSTRUCTION_MESSAGE.value)
        await state.set_state(States.WAITING_FOR_TOKEN)
    elif message_text == "🔙 Назад":
        await message.answer(
            "Возвращаемся в меню...",
            reply_markup=get_bot_menu_keyboard(state_data["bot_id"])
        )
        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer("Напиши ПОДТВЕРДИТЬ для подтверждения удаления или вернись назад")


@router.callback_query(lambda q: q.data.startswith('product:delete'))
async def delete_product_handler(query: CallbackQuery):
    product_id = int(query.data.split("_")[-1])
    await db_engine.get_product_db().delete_product(product_id)
    await query.message.delete()


async def send_instructions(message: Message) -> None:
    file_ids = cache_resources_file_id_store.get_data()
    try:
        await message.answer_media_group(
            media=[
                InputMediaPhoto(media=file_ids["botFather1.jpg"], caption=MessageTexts.INSTRUCTION_MESSAGE.value),
                InputMediaPhoto(media=file_ids["botFather2.jpg"]),
                InputMediaPhoto(media=file_ids["botFather3.jpg"])
            ]
        )
    except (TelegramBadRequest, KeyError) as e:
        logger.info(f"error while sending instructions.... cache is empty, sending raw files {e}")
        media_group = await message.answer_media_group(
            media=[
                InputMediaPhoto(media=FSInputFile(config.RESOURCES_PATH.format("botFather1.jpg")),
                                caption=MessageTexts.INSTRUCTION_MESSAGE.value),
                InputMediaPhoto(media=FSInputFile(config.RESOURCES_PATH.format("botFather2.jpg"))),
                InputMediaPhoto(media=FSInputFile(config.RESOURCES_PATH.format("botFather3.jpg"))),
            ]
        )
        for ind, message in enumerate(media_group, start=1):
            file_ids[f"botFather{ind}.jpg"] = message.photo[0].file_id
        cache_resources_file_id_store.update_data(file_ids)
