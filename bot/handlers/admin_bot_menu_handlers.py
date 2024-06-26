import json
import os
import random
import string
from random import sample
from aiohttp import ClientConnectorError
from datetime import datetime

from aiogram import F, Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from sqlalchemy.exc import IntegrityError
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.fsm.context import FSMContext
from aiogram.utils.token import validate_token, TokenValidationError
from aiogram.fsm.storage.base import StorageKey

from bot.keyboards.channel_keyboards import InlineChannelsListKeyboard
from bot.main import bot, user_db, product_db, order_db, custom_bot_user_db, QUESTION_MESSAGES, bot_db, mailing_db
from bot.utils import MessageTexts
from bot.exceptions import InstanceAlreadyExists
from bot.states.states import States
from bot.handlers.routers import admin_bot_menu_router
from bot.utils.custom_bot_api import start_custom_bot, stop_custom_bot
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard, InlineBotMenuKeyboard, ReplyBackBotMenuKeyboard
from bot.keyboards.stock_menu_keyboards import InlineStockMenuKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard
from bot.keyboards.order_manage_keyboards import InlineOrderStatusesKeyboard, InlineOrderCancelKeyboard, \
    InlineOrderCustomBotKeyboard

from custom_bots.multibot import storage as custom_bot_storage

from database.models.bot_model import BotSchemaWithoutId
from database.models.order_model import OrderSchema, OrderNotFound, OrderItem, OrderStatusValues
from database.models.mailing_model import MailingSchemaWithoutId
from database.models.product_model import ProductWithoutId, NotEnoughProductsInStockToReduce

from logs.config import logger


@admin_bot_menu_router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    try:
        # {'bot_id': '33',
        # 'raw_items':
        #   {'38': {'amount': 4, 'chosen_option': 'на диске'}},
        # 'ordered_at': '2024-05-20T      15:02:42.353Z',
        # 'town': 'sd\nsdsd\n\nsd\n\n',
        # 'address': 'sd', 'comment': ''}

        data = json.loads(event.web_app_data.data)
        logger.info(f"receive web app data: {data}")

        bot_id = data["bot_id"]
        bot_data = await bot_db.get_bot(int(bot_id))

        data["from_user"] = user_id
        data["payment_method"] = "Картой Онлайн"
        data["status"] = "backlog"

        items: dict[int, OrderItem] = {}

        zero_products = []

        for item_id, item in data['raw_items'].items():
            product = await product_db.get_product(item_id)
            chosen_options = {}
            used_options = False
            if 'chosen_option' in item and item['chosen_option']:
                used_options = True
                option_title = list(product.extra_options.items())[0][0]
                chosen_options[option_title] = item['chosen_option']
            items[item_id] = OrderItem(amount=item['amount'], used_extra_option=used_options,
                                       extra_options=chosen_options)
            if bot_data.settings and "auto_reduce" in bot_data.settings and bot_data.settings["auto_reduce"]:
                if product.count < item['amount']:
                    raise NotEnoughProductsInStockToReduce(product, item['amount'])
                product.count -= item['amount']
                if product.count == 0:
                    zero_products.append(product)
                await product_db.update_product(product)

        if zero_products:
            msg = await event.answer("⚠️ Внимание, после этого заказа кол-во следующих товаров будет равно 0.")
            await msg.reply("\n".join([f"{p.name} [{p.id}]" for p in zero_products]))

        data['items'] = items

        date = datetime.now().strftime("%d%m%y")
        random_string = ''.join(random.sample(string.digits + string.ascii_letters, 5))
        data['order_id'] = date + random_string

        order = OrderSchema(**data)

        logger.info(f"order with id #{order.id} created")
    except Exception as e:
        if isinstance(e, NotEnoughProductsInStockToReduce):
            await event.answer(
                f":(\nК сожалению на складе недостаточно <b>{e.product.name}</b> для выполнения Вашего заказа.")
        logger.warning("error while creating order", exc_info=True)
        return await event.answer("Произошла ошибка при создании заказа, попробуйте еще раз.")
    try:
        await send_new_order_notify(order, user_id)
    except Exception as e:
        logger.error("error while sending test order notification", exc_info=e)


@admin_bot_menu_router.message(F.reply_to_message)
async def handle_reply_to_question(message: Message, state: FSMContext):
    question_messages_data = QUESTION_MESSAGES.get_data()
    question_message_id = str(message.reply_to_message.message_id)
    if question_message_id not in question_messages_data:
        logger.info(
            f"{message.from_user.id}: "
            f"replied message with message_id {question_message_id} not found in question_messages_data"
        )
        return await bot_menu_handler(message, state)

    order_id = question_messages_data[question_message_id]["order_id"]
    try:
        order = await order_db.get_order(order_id)
    except OrderNotFound:
        return await message.answer(f"Заказ с номером №{order_id} не найден")

    custom_bot = await bot_db.get_bot_by_created_by(created_by=message.from_user.id)
    await Bot(
        token=custom_bot.token,
        parse_mode=ParseMode.HTML
    ).send_message(
        chat_id=order.from_user,
        text=f"Поступил ответ на вопрос по заказу <b>#{order.id}</b> 👇\n\n"
             f"<i>{message.text}</i>",
        reply_to_message_id=question_messages_data[question_message_id]["question_from_custom_bot_message_id"]
    )
    await message.answer("Ответ отправлен")

    del question_messages_data[question_message_id]
    QUESTION_MESSAGES.update_data(question_messages_data)
    user_state = FSMContext(storage=custom_bot_storage, key=StorageKey(
        chat_id=order.from_user,
        user_id=order.from_user,
        bot_id=bot.id))
    user_state_data = await user_state.get_data()
    if "last_question_time" in user_state_data:
        del user_state_data["last_question_time"]
        await user_state.set_data(user_state_data)


@admin_bot_menu_router.callback_query(lambda query: InlineOrderCancelKeyboard.callback_validator(query.data))
async def handler_order_cancel_callback(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    bot_data = await bot_db.get_bot(state_data['bot_id'])
    bot_token = bot_data.token

    callback_data = InlineOrderCancelKeyboard.Callback.model_validate_json(query.data)

    try:
        order = await order_db.get_order(callback_data.order_id)
    except OrderNotFound:
        await query.answer("Ошибка при работе с заказом, возможно статус уже изменился.", show_alert=True)
        return await query.message.edit_reply_markup(None)

    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_ORDER_STATUSES:
            await query.message.edit_reply_markup(
                reply_markup=InlineOrderStatusesKeyboard.get_keyboard(
                    callback_data.order_id, callback_data.msg_id, callback_data.chat_id, current_status=order.status
                )
            )
        case callback_data.ActionEnum.CANCEL:
            if order.status == OrderStatusValues.CANCELLED:
                return await query.answer("Этот статус уже выставлен")
            order.status = OrderStatusValues.CANCELLED

            await order_db.update_order(order)

            products = [(await product_db.get_product(int(product_id)), product_item.amount, product_item.extra_options)
                        for product_id, product_item in order.items.items()]
            await Bot(bot_token, parse_mode=ParseMode.HTML).edit_message_text(
                order.convert_to_notification_text(products=products),
                reply_markup=None,
                chat_id=callback_data.chat_id,
                message_id=callback_data.msg_id
            )

            username = query.message.text[query.message.text.find("пользователя"):].split()[1].strip("\n")

            await query.message.edit_text(
                text=order.convert_to_notification_text(
                    products=products,
                    username=username,
                    is_admin=True
                ), reply_markup=None
            )

            for item_id, item in order.items.items():
                product = await product_db.get_product(item_id)
                product.count += item.amount
                await product_db.update_product(product)

            await Bot(bot_token, parse_mode=ParseMode.HTML).send_message(
                chat_id=callback_data.chat_id,
                text=f"Новый статус заказа <b>#{order.id}</b>\n<b>{order.translate_order_status()}</b>"
            )


@admin_bot_menu_router.callback_query(lambda query: InlineOrderStatusesKeyboard.callback_validator(query.data))
async def handle_callback(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    bot_data = await bot_db.get_bot(state_data['bot_id'])
    bot_token = bot_data.token

    callback_data = InlineOrderStatusesKeyboard.Callback.model_validate_json(query.data)

    try:
        order = await order_db.get_order(callback_data.order_id)
    except OrderNotFound:
        await query.answer("Ошибка при работе с заказом, возможно статус уже изменился.", show_alert=True)
        return await query.message.edit_reply_markup(None)

    match callback_data.a:
        case callback_data.ActionEnum.PRE_CANCEL:
            await query.message.edit_reply_markup(
                reply_markup=InlineOrderCancelKeyboard.get_keyboard(
                    callback_data.order_id, callback_data.msg_id, callback_data.chat_id
                )
            )
        case callback_data.ActionEnum.FINISH \
             | callback_data.ActionEnum.PROCESS \
             | callback_data.ActionEnum.BACKLOG \
             | callback_data.ActionEnum.WAITING_PAYMENT:  # noqa
            new_status = {
                callback_data.ActionEnum.FINISH: OrderStatusValues.FINISHED,
                callback_data.ActionEnum.PROCESS: OrderStatusValues.PROCESSING,
                callback_data.ActionEnum.BACKLOG: OrderStatusValues.BACKLOG,
                callback_data.ActionEnum.WAITING_PAYMENT: OrderStatusValues.WAITING_PAYMENT
            }[callback_data.a]

            if order.status == new_status:
                return await query.answer("Этот статус уже выставлен")
            order.status = new_status

            await order_db.update_order(order)

            products = [(await product_db.get_product(int(product_id)), product_item.amount, product_item.extra_options)
                        for product_id, product_item in order.items.items()]
            await Bot(bot_token, parse_mode=ParseMode.HTML).edit_message_text(
                order.convert_to_notification_text(products=products),
                reply_markup=None if callback_data.a == callback_data.ActionEnum.FINISH else
                InlineOrderCustomBotKeyboard.get_keyboard(order.id, callback_data.msg_id, callback_data.chat_id),
                chat_id=callback_data.chat_id,
                message_id=callback_data.msg_id
            )

            username = query.message.text[query.message.text.find("пользователя"):].split()[1].strip("\n")

            await query.message.edit_text(
                text=order.convert_to_notification_text(
                    products=products,
                    username=username,
                    is_admin=True
                ), reply_markup=None if callback_data.a == callback_data.ActionEnum.FINISH else
                InlineOrderStatusesKeyboard.get_keyboard(
                    order.id, callback_data.msg_id, callback_data.chat_id, order.status)
            )

            if callback_data.a == callback_data.ActionEnum.FINISH:
                if bot_data.settings and "auto_reduce" in bot_data.settings and \
                        bot_data.settings['auto_reduce']:
                    zero_products = []
                    for item_id, item in order.items.items():
                        product = await product_db.get_product(item_id)
                        if product.count == 0:
                            zero_products.append(product)
                    if zero_products:
                        msg = await query.message.answer(
                            "⚠️ Внимание, кол-во следующих товаров на складе равно 0.")
                        await msg.reply("\n".join([f"{p.name} [{p.id}]" for p in zero_products]))

            await Bot(bot_token, parse_mode=ParseMode.HTML).send_message(
                chat_id=callback_data.chat_id,
                text=f"Новый статус заказа <b>#{order.id}</b>\n<b>{order.translate_order_status()}</b>")


@admin_bot_menu_router.message(States.WAITING_FOR_TOKEN)
async def waiting_for_the_token_handler(message: Message, state: FSMContext):
    user = await user_db.get_user(message.from_user.id)
    lang = user.locale
    token = message.text
    try:
        validate_token(token)

        found_bot = Bot(token)
        found_bot_data = await found_bot.get_me()
        bot_fullname, bot_username = found_bot_data.full_name, found_bot_data.username

        new_bot = BotSchemaWithoutId(
            bot_token=token,
            status="new",
            created_at=datetime.utcnow(),
            created_by=message.from_user.id,
            settings={"start_msg": MessageTexts.DEFAULT_START_MESSAGE.value,
                      "default_msg":
                          f"Приветствую, этот бот создан с помощью @{(await bot.get_me()).username}",
                      "web_app_button": MessageTexts.OPEN_WEB_APP_BUTTON_TEXT.value},
            locale=lang
        )

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
    except Exception as e:
        logger.error(
            f"Unexpected error while adding new bot with token {token} from user {message.from_user.id}", exc_info=e
        )
        return await message.answer(":( Произошла ошибка при добавлении бота, попробуйте еще раз позже")
    user_bot = await bot_db.get_bot(bot_id)
    await message.answer(
        MessageTexts.BOT_INITIALIZING_MESSAGE.value.format(bot_fullname, bot_username),
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
    )
    await message.answer(
        MessageTexts.BOT_MENU_MESSAGE.value.format(bot_username),
        reply_markup=await InlineBotMenuKeyboard.get_keyboard(user_bot.bot_id)
    )
    await state.set_state(States.BOT_MENU)
    await state.set_data({"bot_id": bot_id})


@admin_bot_menu_router.message(States.BOT_MENU, F.photo)
async def bot_menu_photo_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    photo_file_id = message.photo[-1].file_id

    if message.caption is None:
        return await message.answer("Чтобы добавить товар, прикрепите его картинку и отправьте сообщение в виде:"
                                    "\n\nНазвание\nЦена в рублях")

    params = message.caption.strip().split('\n')
    filename = "".join(sample(string.ascii_letters + string.digits, k=5)) + ".jpg"

    if len(params) != 2:
        return await message.answer("Чтобы добавить товар, прикрепите его картинку и отправьте сообщение в виде:"
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
                                   picture=[filename],
                                   article=params[0],
                                   category=[0],
                                   extra_options={})
    try:
        await product_db.add_product(new_product)
    except IntegrityError:
        return await message.answer("Товар с таким названием уже есть в боте.")
    await message.answer("Товар добавлен. Можно добавить ещё")


@admin_bot_menu_router.callback_query(lambda query: InlineBotMenuKeyboard.callback_validator(query.data))
async def bot_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    callback_data = InlineBotMenuKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id

    match callback_data.a:
        case callback_data.ActionEnum.BOT_EDIT_HELLO_TEXT:
            await query.message.answer(
                "Введите текст, который будет отображаться у пользователей Вашего бота "
                "при <b>первом обращении</b> и команде <b>/start</b>:",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_START_MESSAGE)
            await state.set_data(state_data)
        case callback_data.ActionEnum.BOT_EDIT_EXPLANATION_TEXT:
            await query.message.answer(
                "Введите текст, который будет отображаться у пользователей Вашего бота "
                "при <b>любом</b> их сообщении: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_DEFAULT_MESSAGE)
            await state.set_data(state_data)
        case callback_data.ActionEnum.BOT_START:
            await start_custom_bot(bot_id)
            await query.message.edit_text(
                query.message.text,
                parse_mode=ParseMode.HTML,
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(bot_id)
            )
            await query.answer("Ваш бот запущен ✅", show_alert=True)
        case callback_data.ActionEnum.BOT_STOP:
            await stop_custom_bot(bot_id)
            await query.message.edit_text(
                query.message.text,
                parse_mode=ParseMode.HTML,
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(bot_id)
            )
            await query.answer("Ваш бот приостановлен ❌", show_alert=True)
        case callback_data.ActionEnum.BOT_DELETE:
            await query.message.answer(
                "Бот удалится вместе со всей базой продуктов безвозвратно.\n"
                "Напишите ПОДТВЕРДИТЬ для подтверждения удаления",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard())
            await query.answer()

            await state.set_state(States.DELETE_BOT)
            await state.set_data(state_data)
        case callback_data.ActionEnum.BOT_STATISTICS:
            users = await custom_bot_user_db.get_custom_bot_users(bot_id=bot_id)
            await query.message.answer(
                f"Статистика:\n\n"
                f"👨🏻‍🦱 Всего пользователей: {len(users)}"
            )
            await query.answer()
        case callback_data.ActionEnum.MAILING_ADD | InlineBotMenuKeyboard.Callback.ActionEnum.MAILING_OPEN:
            if callback_data.a == InlineBotMenuKeyboard.Callback.ActionEnum.MAILING_ADD:
                await mailing_db.add_mailing(MailingSchemaWithoutId.model_validate(
                    {"bot_id": bot_id, "created_at": datetime.now().replace(tzinfo=None)}
                ))
            custom_bot = await bot_db.get_bot(bot_id=bot_id)
            await query.message.edit_text(
                MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id=bot_id)
            )
        case callback_data.ActionEnum.BOT_GOODS_OPEN:
            bot_data = await bot_db.get_bot(bot_id)
            if not bot_data.settings or "auto_reduce" not in bot_data.settings:
                auto_reduce = False
            else:
                auto_reduce = True
            await query.message.edit_text(
                "Меню склада:",
                reply_markup=await InlineStockMenuKeyboard.get_keyboard(bot_id, auto_reduce)
            )
        case callback_data.ActionEnum.CHANNEL_LIST:
            custom_bot = await bot_db.get_bot(bot_id)

            await query.message.edit_text(
                MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineChannelsListKeyboard.get_keyboard(custom_bot.bot_id)
            )


@admin_bot_menu_router.message(States.BOT_MENU)
async def bot_menu_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    custom_bot = await bot_db.get_bot(state_data['bot_id'])

    match message.text:
        case ReplyBotMenuKeyboard.Callback.ActionEnum.SHOP.value:
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id)
            )

        case ReplyBotMenuKeyboard.Callback.ActionEnum.CONTACTS.value:
            await message.answer(
                MessageTexts.CONTACTS.value
            )
        case _:
            await message.answer(
                "Для навигации используйте кнопки 👇",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id)
            )


async def send_new_order_notify(order: OrderSchema, user_id: int):
    order_user_data = await bot.get_chat(order.from_user)
    products = [(await product_db.get_product(product_id), product_item.amount, product_item.extra_options)
                for product_id, product_item in order.items.items()]

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
