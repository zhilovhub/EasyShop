import os
from re import fullmatch
from datetime import datetime
from distutils.dir_util import copy_tree

from bot.main import bot, db_engine

from aiogram import Router, Bot
from aiogram.types import Message, MenuButtonWebApp, WebAppInfo, ReplyKeyboardRemove, FSInputFile, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.fsm.context import FSMContext

from bot import config
from bot.config import logger
from bot.keyboards import get_bot_menu_keyboard, get_back_keyboard, get_inline_delete_button
from bot.states.states import States
from bot.locales.default import DefaultLocale
from bot.filters.chat_type import ChatTypeFilter
from bot.exceptions.exceptions import *

from database.models.bot_model import BotSchema
from database.models.user_model import UserSchema
from database.models.product_model import ProductWithoutId
from database.models.order_model import OrderSchema, OrderNotFound

from magic_filter import F

import json

router = Router(name="users")
router.message.filter(ChatTypeFilter(chat_type='private'))

product_db = db_engine.get_product_db()
order_db = db_engine.get_order_dao()
bot_db = db_engine.get_bot_dao()


async def send_new_order_notify(order: OrderSchema, user_id: int):
    order_user_data = await bot.get_chat(order.from_user)

    await bot.send_message(user_id, f"Так будет выглядеть у тебя уведомление о новом заказе 👇")
    await bot.send_message(
        user_id, order.convert_to_notification_text(
            [await product_db.get_product(product_id) for product_id in order.products_id],
            "@" + order_user_data.username if order_user_data.username else order_user_data.full_name,
            True
        )
    )
    await order_db.delete_order(order.id)


async def send_order_change_status_notify(order: OrderSchema):
    user_bot = await bot_db.get_bot(order.bot_token)
    text = f"Новый статус заказ <b>#{order.id}</b>\n<b>{order.status}</b>"
    await bot.send_message(user_bot.created_by, text)
    await bot.send_message(order.from_user, text)


@router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    try:
        data = json.loads(event.web_app_data.data)
        logger.info(f"recieve web app data: {data}")

        order = await order_db.get_order(data['order_id'])
        order.from_user = user_id
        await order_db.update_order(order)

        logger.info(f"order found")
    except OrderNotFound:
        logger.info("order_not_found")
        return

    try:
        await send_new_order_notify(order, user_id)
    except Exception as e:
        logger.info(e)


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
        user_bot = Bot(user_bots[0].token)
        user_bot_data = await user_bot.get_me()
        await message.answer(DefaultLocale.selected_bot_msg().replace("{selected_name}", user_bot_data.full_name),
                             reply_markup=get_bot_menu_keyboard(WebAppInfo(
                                 url=config.WEB_APP_URL + '?token=' + user_bot.token.replace(':', '_'))))
        await state.set_state(States.BOT_MENU)
        await state.set_data({'token': user_bots[0].token})


@router.message(States.WAITING_FOR_TOKEN)  # TODO remove all replace(":", "___") of tokens
async def waiting_for_the_token_handler(message: Message, state: FSMContext):
    user = await db_engine.get_user_dao().get_user(message.from_user.id)
    lang = user.locale
    token = message.text
    if fullmatch(r"\d{10}:[\w|-]{35}", token.replace("_", "a")):
        try:
            found_bot = Bot(token)
            found_bot_data = await found_bot.get_me()
            try:
                await db_engine.get_bot_dao().get_bot(token)  # TODO сделать список ботов после MVP
                await message.answer("Бот с таким токеном в системе уже найден.\n"
                                     "Введи другой токен или перейди в список ботов и поищи своего бота там")
            except Exception:
                bot_fullname, bot_username = found_bot_data.full_name, found_bot_data.username
                new_bot = BotSchema(bot_token=token,
                                    status="new",
                                    created_at=datetime.utcnow(),
                                    created_by=message.from_user.id,
                                    settings={"start_msg": DefaultLocale.default_start_msg(),
                                              "default_msg": "Привет, этот бот создан с помощью @here_should_be_bot",
                                              "web_app_button": DefaultLocale.open_web_app_button()},
                                    locale=lang)

                working_directory = os.getcwd()
                copy_tree(f'{working_directory}/template', f'{working_directory}/bots/bot{token.replace(":", "___")}')
                os.system(f"mkdir {working_directory}/bots/bot{token.replace(':', '___')}/logs")
                logger.info(f'successfully create new sub bot files in directory bots/bot{token.replace(":", "___")}')
                with open(f'{working_directory}/bots/bot{token.replace(":", "___")}/.env', 'w') as envfile:
                    envfile.write(f"TELEGRAM_TOKEN={token}"
                                  f"\nDB_URL={config.DB_URL}"
                                  f"\nWEB_APP_URL={config.WEB_APP_URL}?token={token.replace(':', '_')}")
                logger.info(f'successfully .env sub bot file in directory bots/bot{token.replace(":", "___")}/.env')
                with open(f'{working_directory}/bots/bot{token.replace(":", "___")}/bot.service', 'r') as servicefile:
                    txt = servicefile.read().replace('{working_directory}',
                                                     f'{working_directory}/bots/bot{token.replace(":", "___")}')
                with open(f'{working_directory}/bots/bot{token.replace(":", "___")}/bot.service', 'w') as servicefile:
                    servicefile.write(txt)

                await found_bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(text=DefaultLocale.open_web_app_button(),
                                                 web_app=WebAppInfo(
                                                     url=config.WEB_APP_URL + '?token=' + token.replace(':', '_')))
                )

                logger.debug("added web_app button to bot menu.")
                os.system(
                    f"echo -e {os.getenv('PASSWORD')} | "
                    f"sudo -S cp {working_directory}/bots/bot{token.replace(':', '___')}/bot.service "
                    f"/etc/systemd/system/bot{token.replace(':', '___')}.service")
                os.system(f"echo -e {os.getenv('PASSWORD')} | sudo -S -k systemctl daemon-reload")
                os.system(f"echo -e {os.getenv('PASSWORD')} | "
                          f"sudo -S -k systemctl start bot{token.replace(':', '___')}.service")

                await db_engine.get_bot_dao().add_bot(new_bot)

                await message.answer(
                    DefaultLocale.bot_will_initialize().format(bot_fullname, bot_username),
                    reply_markup=get_bot_menu_keyboard(WebAppInfo(
                        url=config.WEB_APP_URL + '?token=' + token.replace(':', '_')))
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data({"token": token})

        except TelegramUnauthorizedError:
            await message.answer(DefaultLocale.bot_with_token_not_found())

        except Exception:
            logger.error(f"Error while adding new bot wit token {token} from user {message.from_user.id}",
                         exc_info=True)
            await message.answer("Unknown error while adding bot")
    else:
        await message.answer(DefaultLocale.incorrect_bot_token())


@router.message(States.BOT_MENU, F.photo)
async def bot_menu_photo_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    photo_file_id = message.photo[-1].file_id
    params = message.caption.strip().split('\n')

    if len(params) != 2:
        return await message.answer("Чтобы добавить товар, прикрепи его картинку и отправь сообщение в виде:"
                                    "\n\nНазвание\nЦена в рублях")
    try:
        price = float(params[-1].replace(",", "."))
    except ValueError:
        return await message.answer("Цена должна быть в формате: <b>100.00</b>")

    await bot.download(photo_file_id, destination=f"Files/img/{state_data['token']}__{params[0]}.jpg")
    with open(f"Files/img/{state_data['token']}__{params[0]}.jpg", 'rb') as photo_file:
        photo_bytes = photo_file.read()

    new_product = ProductWithoutId(bot_token=state_data['token'],
                                   name=params[0],
                                   description="",
                                   price=price,
                                   picture=f"bot/Files/img/{state_data['token']}__{params[0]}.jpg")
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
            products = await db_engine.get_product_db().get_all_products(state_data["token"])
            if not products:
                await message.answer("Список товаров твоего магазина пуст")
            else:
                await message.answer("Список товаров твоего магазина 👇\nЧтобы удалить товар, нажми на тег рядом с ним")
                for product in products:
                    await message.answer_photo(
                        photo=FSInputFile("../" + product.picture),
                        caption=f"<b>{product.name}</b>\n\n"
                                f"Цена: <b>{float(product.price)}₽</b>",
                        reply_markup=get_inline_delete_button(product.id))
        case "Добавить товар":
            await message.answer("Чтобы добавить товар, прикрепи его картинку и отправь сообщение в виде:"
                                 "\n\nНазвание\nЦена в рублях")
        case "Запустить бота":
            os.system(f"echo -e {os.getenv('PASSWORD')} | sudo -S -k systemctl restart "
                      f"bot{state_data['token'].replace(':', '___')}.service")
            await message.answer("Твой бот запущен ✅")
        case "Остановить бота":
            os.system(f"echo -e {os.getenv('PASSWORD')} | sudo -S -k systemctl stop "
                      f"bot{state_data['token'].replace(':', '___')}.service")
            await message.answer("Твой бот приостановлен ❌")
        case "Удалить бота":
            os.system(f"echo -e {os.getenv('PASSWORD')} | sudo -S -k systemctl stop "
                      f"bot{state_data['token'].replace(':', '___')}.service")
            await message.answer("Бот удалится вместе со всей базой продуктов безвозвратно.\n"
                                 "Напиши ПОДТВЕРДИТЬ для подтверждения удаления", reply_markup=get_back_keyboard())
            await state.set_state(States.DELETE_BOT)
            await state.set_data(state_data)
        case _:
            await message.answer(
                "Для навигации используй кнопки 👇",
                reply_markup=get_bot_menu_keyboard(
                    WebAppInfo(url=config.WEB_APP_URL + f"?token={state_data['token']}".replace(":", "_"))))


@router.message(States.EDITING_START_MESSAGE)
async def editing_start_message_handler(message: Message, state: FSMContext):
    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращемся в меню...",
                reply_markup=get_bot_menu_keyboard(WebAppInfo(
                    url=config.WEB_APP_URL + '?token=' + state_data['token'].replace(':', '_'))))
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            user_bot = await db_engine.get_bot_dao().get_bot(state_data["token"])
            if user_bot.settings:
                user_bot.settings["start_msg"] = message_text
            else:
                user_bot.settings = {"start_msg": message_text}
            await db_engine.get_bot_dao().update_bot(user_bot)

            await message.answer(
                "Стартовое сообщение изменено!",
                reply_markup=get_bot_menu_keyboard(WebAppInfo(
                    url=config.WEB_APP_URL + '?token=' + state_data['token'].replace(':', '_'))))
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
                reply_markup=get_bot_menu_keyboard(WebAppInfo(
                    url=config.WEB_APP_URL + '?token=' + state_data['token'].replace(':', '_'))))
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            user_bot = await db_engine.get_bot_dao().get_bot(state_data["token"])
            if user_bot.settings:
                user_bot.settings["default_msg"] = message_text
            else:
                user_bot.settings = {"default_msg": message_text}
            await db_engine.get_bot_dao().update_bot(user_bot)

            await message.answer(
                "Сообщение-затычка изменена!",
                reply_markup=get_bot_menu_keyboard(WebAppInfo(
                    url=config.WEB_APP_URL + '?token=' + state_data['token'].replace(':', '_'))))
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
    else:
        await message.answer("Сообщение-затычка должна содержать текст")


@router.message(States.DELETE_BOT)
async def delete_bot_handler(message: Message, state: FSMContext):
    message_text = message.text
    state_data = await state.get_data()
    if message_text == "ПОДТВЕРДИТЬ":
        await db_engine.get_bot_dao().del_bot(state_data["token"])

        await message.answer(
            "Бот удален",
            reply_markup=ReplyKeyboardRemove())
        await message.answer(DefaultLocale.input_token())
        await state.set_state(States.WAITING_FOR_TOKEN)
    elif message_text == "🔙 Назад":
        await message.answer(
            "Возвращемся в меню...",
            reply_markup=get_bot_menu_keyboard(
                WebAppInfo(url=config.WEB_APP_URL + f"?token={state_data['token']}".replace(":", "_"))))
        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer("Напиши ПОДТВЕРДИТЬ для подтверждения удаления или вернись назад")


@router.callback_query(lambda q: q.data.startswith('product:delete'))
async def delete_product_handler(query: CallbackQuery):
    product_id = int(query.data.split("_")[-1])
    await db_engine.get_product_db().delete_product(product_id)
    await query.message.delete()
