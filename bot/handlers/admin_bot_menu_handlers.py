import json
import os
import string
from random import sample
from datetime import datetime

from aiogram.fsm.storage.base import StorageKey
from aiohttp import ClientConnectorError

from aiogram import Bot, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.utils.token import validate_token, TokenValidationError

from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.main import bot, user_db, bot_db, product_db, order_db, custom_bot_user_db, QUESTION_MESSAGES
from bot.config import logger
from bot.keyboards import *
from bot.exceptions import InstanceAlreadyExists
from bot.states.states import States
from bot.handlers.routers import admin_bot_menu_router
from bot.utils.custom_bot_api import start_custom_bot, stop_custom_bot
from sqlalchemy.exc import IntegrityError

from custom_bots.multibot import storage as custom_bot_storage

from database.models.bot_model import BotSchemaWithoutId
from database.models.order_model import OrderSchema, OrderNotFound, OrderItem
from database.models.product_model import ProductWithoutId

import random


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

        data["from_user"] = user_id
        data["payment_method"] = "Картой Онлайн"
        data["status"] = "backlog"

        items: dict[int, OrderItem] = {}

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

        data['items'] = items

        date = datetime.now().strftime("%d%m%y")
        random_string = ''.join(random.sample(string.digits + string.ascii_letters, 5))
        data['order_id'] = date + random_string

        order = OrderSchema(**data)

        logger.info(f"order with id #{order.id} created")
    except Exception:
        logger.warning("error while creating order", exc_info=True)
        return await event.answer("Произошла ошибка при создании заказа, попробуйте еще раз.")

    try:
        await send_new_order_notify(order, user_id)
    except Exception as ex:
        logger.warning("error while sending test order notification", exc_info=True)


@admin_bot_menu_router.message(F.reply_to_message)
async def handle_reply_to_question(message: Message, state: FSMContext):
    question_messages_data = QUESTION_MESSAGES.get_data()
    question_message_id = str(message.reply_to_message.message_id)
    if not question_message_id in question_messages_data:
        logger.info(
            f"{message.from_user.id}: replied message with message_id {question_message_id} not found in question_messages_data"
        )
        return await bot_menu_handler(message, state)

    order_id = question_messages_data[question_message_id]["order_id"]
    try:
        order = await order_db.get_order(order_id)
    except OrderNotFound:
        return await message.answer(f"Заказ с номером №{order_id} не найден")

    custom_bot = await bot_db.get_bot_by_created_by(created_by=message.from_user.id)
    await Bot(token=custom_bot.token, parse_mode=ParseMode.HTML).send_message(chat_id=order.from_user,
                                                                              text=f"Поступил ответ на вопрос по заказу <b>#{order.id}</b> 👇\n\n"
                                                                                   f"<i>{message.text}</i>",
                                                                              reply_to_message_id=
                                                                              question_messages_data[
                                                                                  question_message_id][
                                                                                  "question_from_custom_bot_message_id"])
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


@admin_bot_menu_router.callback_query(lambda q: q.data.startswith("order_"))
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
            new_status = {
                "order_cancel": OrderStatusValues.CANCELLED,
                "order_finish": OrderStatusValues.FINISHED,
                "order_process": OrderStatusValues.PROCESSING,
                "order_backlog": OrderStatusValues.BACKLOG,
                "order_waiting_payment": OrderStatusValues.WAITING_PAYMENT
            }[data[0]]

            if order.status == new_status:
                return await query.answer("Этот статус уже выставлен")
            order.status = new_status

            await order_db.update_order(order)

            products = [(await product_db.get_product(int(product_id)), product_item.amount, product_item.extra_options)
                        for product_id, product_item in order.items.items()]
            await Bot(bot_token, parse_mode=ParseMode.HTML).edit_message_text(
                order.convert_to_notification_text(products=products),
                reply_markup=None if data[0] in ("order_finish", "order_cancel") else
                create_user_order_kb(order.id, int(data[2]), int(data[3])),
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
        reply_markup=get_reply_bot_menu_keyboard(bot_id)
    )
    await message.answer(
        MessageTexts.BOT_MENU_MESSAGE.value.format(bot_username),
        reply_markup=await get_inline_bot_menu_keyboard(user_bot.bot_id)
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
                                   picture=filename,
                                   article=params[0],
                                   category=[0])
    try:
        await product_db.add_product(new_product)
    except IntegrityError:
        return await message.answer("Товар с таким названием уже есть в боте.")
    await message.answer("Товар добавлен. Можно добавить ещё")


@admin_bot_menu_router.callback_query(lambda query: query.data.startswith("bot_menu"))
async def bot_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    query_data = query.data.split(":")[1]

    match query_data:
        case "start_text":
            await query.message.answer("Введите текст, который будет отображаться у пользователей Вашего бота "
                                       "при <b>первом обращении</b> и команде <b>/start</b>:",
                                       reply_markup=get_back_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_START_MESSAGE)
            await state.set_data(state_data)
        case "explain_text":
            await query.message.answer("Введите текст, который будет отображаться у пользователей Вашего бота "
                                       "при <b>любом</b> их сообщении: ", reply_markup=get_back_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_DEFAULT_MESSAGE)
            await state.set_data(state_data)
        case "start_bot":
            await start_custom_bot(state_data['bot_id'])
            await query.message.edit_text(
                query.message.text,
                parse_mode=ParseMode.HTML,
                reply_markup=await get_inline_bot_menu_keyboard(state_data['bot_id'])
            )
            await query.answer("Ваш бот запущен ✅", show_alert=True)
        case "stop_bot":
            await stop_custom_bot(state_data['bot_id'])
            await query.message.edit_text(
                query.message.text,
                parse_mode=ParseMode.HTML,
                reply_markup=await get_inline_bot_menu_keyboard(state_data['bot_id'])
            )
            await query.answer("Ваш бот приостановлен ❌", show_alert=True)
        case "delete_bot":
            await query.message.answer("Бот удалится вместе со всей базой продуктов безвозвратно.\n"
                                       "Напишите ПОДТВЕРДИТЬ для подтверждения удаления",
                                       reply_markup=get_back_keyboard())
            await query.answer()

            await state.set_state(States.DELETE_BOT)
            await state.set_data(state_data)
        case "statistic":
            users = await custom_bot_user_db.get_custom_bot_users(bot_id=state_data["bot_id"])
            await query.message.answer(
                f"Статистика:\n\n"
                f"👨🏻‍🦱 Всего пользователей: {len(users)}"
            )
            await query.answer()
        case "goods":
            await query.message.edit_text("Меню склада:", reply_markup=get_inline_bot_goods_menu_keyboard(state_data['bot_id']))
        case "goods_count":
            products = await product_db.get_all_products(state_data["bot_id"])
            await query.message.answer(f"Количество товаров: {len(products)}")
            await query.answer()
        case "goods_list":
            products = await product_db.get_all_products(state_data["bot_id"])
            if not products:
                await query.message.answer("Список товаров Вашего магазина пуст")
            else:
                await query.message.answer(
                    "Список товаров Вашего магазина 👇\nЧтобы удалить товар, нажмите на тег рядом с ним")
                for product in products:
                    await query.message.answer_photo(
                        photo=FSInputFile(os.getenv('FILES_PATH') + product.picture),
                        caption=f"<b>{product.name}</b>\n\n"
                                f"Цена: <b>{float(product.price)}₽</b>",
                        reply_markup=get_inline_delete_button(product.id))
            await query.answer()
        case "add_new_good":
            await query.message.answer("Чтобы добавить товар, прикрепите его картинку и отправьте сообщение в виде:"
                                       "\n\nНазвание\nЦена в рублях")
            await query.answer()
        case "back_to_menu":
            custom_bot = await bot_db.get_bot(state_data['bot_id'])
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
            )
        case "channels":
            custom_bot = await bot_db.get_bot(state_data["bot_id"])
            await query.message.edit_text(
                MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await get_inline_bot_channels_list_keyboard(custom_bot.bot_id)
            )
        case "channel":
            custom_bot = await bot_db.get_bot(state_data["bot_id"])
            custom_tg_bot = Bot(custom_bot.token)
            channel_id = int(query.data.split(":")[-1])
            channel_username = (await custom_tg_bot.get_chat(channel_id)).username
            await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(channel_username, (await custom_tg_bot.get_me()).username),
                reply_markup=await get_inline_channel_menu_keyboard(custom_bot.bot_id, int(query.data.split(":")[-1]))
            )


@admin_bot_menu_router.message(States.BOT_MENU)
async def bot_menu_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    custom_bot = await bot_db.get_bot(state_data['bot_id'])

    match message.text:
        case ReplyBotMenuButtons.SETTINGS.value:
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
            )

        case ReplyBotMenuButtons.CONTACTS.value:
            await message.answer(
                MessageTexts.CONTACTS.value
            )
        case _:
            await message.answer(
                "Для навигации используйте кнопки 👇",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
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
