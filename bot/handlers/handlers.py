import os
import string
from random import sample
from re import fullmatch
from datetime import datetime
from distutils.dir_util import copy_tree

from bot.main import bot, db_engine

from aiogram import Router, Bot
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.utils.token import TokenValidationError, validate_token

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError

from bot import config
from bot.config import logger
from bot.keyboards import *
from bot.states.states import States
from bot.locales.default import DefaultLocale
from bot.filters.chat_type import ChatTypeFilter
from bot.exceptions.exceptions import *

from database.models.bot_model import BotSchemaWithoutId
from database.models.user_model import UserSchema
from database.models.order_model import OrderSchema, OrderNotFound, OrderStatusValues
from database.models.product_model import ProductWithoutId

from magic_filter import F

import json

router = Router(name="users")
router.message.filter(ChatTypeFilter(chat_type='private'))

product_db = db_engine.get_product_db()
order_db = db_engine.get_order_dao()
bot_db = db_engine.get_bot_dao()


async def start_custom_bot(token: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"http://{config.LOCAL_API_SERVER_HOST}:{config.LOCAL_API_SERVER_PORT}/start_bot/{token}") as response:
            if response.status != 200:
                raise LocalAPIException(f"API returned {response.status} status code "
                                        f"with text {await response.text()}")


async def stop_custom_bot(token: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"http://{config.LOCAL_API_SERVER_HOST}:{config.LOCAL_API_SERVER_PORT}/stop_bot/{token}") as response:
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
                data[1], int(data[2]), int(data[3])))
        case "order_finish" | "order_cancel" | "order_process" | "order_backlog":
            order.status, is_processing = {
                "order_cancel": (OrderStatusValues.CANCELLED, False),
                "order_finish": (OrderStatusValues.FINISHED, False),
                "order_process": (OrderStatusValues.PROCESSING, True),
                "order_backlog": (OrderStatusValues.BACKLOG, False),
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

            await query.message.edit_text(
                text=order.convert_to_notification_text(
                    products=products,
                    username="@" + query.from_user.username if query.from_user.username else query.from_user.full_name,
                    is_admin=True
                ), reply_markup=None if data[0] in ("order_finish", "order_cancel") else
                create_change_order_status_kb(order.id, int(data[2]), int(data[3]), is_processing))

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

        order = OrderSchema(**data)

        logger.info(f"order with id #{order.id} created")
    except Exception:
        logger.warning("error while creating order", exc_info=True)
        return await event.answer("Произошла ошибка при создании заказа, попробуйте еще раз.")

    try:
        await send_new_order_notify(order, user_id)
    except Exception as ex:
        logger.warning("error while sending test order notification", exc_info=True)


@router.message(CommandStart())
async def start_command_handler(message: Message, state: FSMContext):
    try:
        await db_engine.get_user_dao().get_user(message.from_user.id)
    except UserNotFound:
        logger.info(f"user {message.from_user.id} not found in db, creating new instance...")

        await db_engine.get_user_dao().add_user(UserSchema(
            user_id=message.from_user.id, registered_at=datetime.utcnow(), status="new", locale="default")
        )

    await message.answer(DefaultLocale.about_message())

    user_bots = await db_engine.get_bot_dao().get_bots(message.from_user.id)
    if not user_bots:
        await state.set_state(States.WAITING_FOR_TOKEN)
        await message.answer(DefaultLocale.input_token())
    else:
        bot_id = user_bots[0].bot_id
        user_bot = Bot(bot_id)
        user_bot_data = await user_bot.get_me()
        await message.answer(DefaultLocale.selected_bot_msg().replace("{selected_name}", user_bot_data.full_name),
                             reply_markup=get_bot_menu_keyboard(bot_id=bot_id))
        await state.set_state(States.BOT_MENU)
        await state.set_data({'bot_id': bot_id})  # TODO change token to bot_id


@router.message(States.WAITING_FOR_TOKEN)  # TODO remove all replace(":", "___") of tokens
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
                            settings={"start_msg": DefaultLocale.default_start_msg(),
                                      "default_msg":
                                          f"Привет, этот бот создан с помощью @{(await bot.get_me()).username}",
                                      "web_app_button": DefaultLocale.open_web_app_button()},
                            locale=lang)

        await bot_db.add_bot(new_bot)
        await start_custom_bot(token)
    except TokenValidationError:
        return await message.answer(DefaultLocale.incorrect_bot_token())
    except TelegramUnauthorizedError:
        return await message.answer(DefaultLocale.bot_with_token_not_found())
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
        DefaultLocale.bot_will_initialize().format(bot_fullname, bot_username),
        reply_markup=get_bot_menu_keyboard(WebAppInfo(
            url=config.WEB_APP_URL + '?token=' + token.replace(':', '_')))
    )
    await state.set_state(States.BOT_MENU)
    await state.set_data({"token": token})


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
            await start_custom_bot(state_data['token'])
            await message.answer("Твой бот запущен ✅")
        case "Остановить бота":
            await stop_custom_bot(state_data['token'])
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
                "Возвращемся в меню...",
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
                "Возвращемся в меню...",
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
        logger.info(f"Disabling bot {state_data['token']}, setting deleted status to db...")
        user_bot = await bot_db.get_bot(state_data["token"])
        user_bot.status = "Deleted"
        await bot_db.del_bot(user_bot.bot_id)

        await message.answer(
            "Бот удален",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(DefaultLocale.input_token())
        await state.set_state(States.WAITING_FOR_TOKEN)
    elif message_text == "🔙 Назад":
        await message.answer(
            "Возвращемся в меню...",
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
