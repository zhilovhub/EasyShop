import os
from re import fullmatch
from datetime import datetime
from distutils.dir_util import copy_tree

from bot.main import bot, db_engine

from aiogram import Router, Bot
from aiogram.types import Message, MenuButtonWebApp, WebAppInfo, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.fsm.context import FSMContext

from bot import config
from bot.main import db
from bot.utils import DbUser, DbBot
from bot.config import logger
from bot.keyboards import get_bot_menu_keyboard, get_back_keyboard
from bot.states.states import States
from bot.locales.default import DefaultLocale
from bot.filters.chat_type import ChatTypeFilter
from bot.exceptions.exceptions import *
from database.models.product_model import ProductWithoutId

router = Router(name="users")
router.message.filter(ChatTypeFilter(chat_type='private'))


@router.message(CommandStart())
async def start_command_handler(message: Message, state: FSMContext):
    try:
        await db.get_user(message.from_user.id)
    except UserNotFound:
        logger.info(f"user {message.from_user.id} not found in db, creating new instance...")

        await db.add_user(DbUser(
            user_id=message.from_user.id, registered_at=datetime.utcnow(), status="new", locale="default")
        )

    await message.answer(DefaultLocale.about_message())
    await message.answer(DefaultLocale.input_token())

    await state.set_state(States.WAITING_FOR_TOKEN)


@router.message(States.WAITING_FOR_TOKEN)  # TODO remove all replace(":", "___") of tokens
async def waiting_for_the_token_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.locale
    token = message.text
    if fullmatch(r"\d{10}:\w{35}", token):
        try:
            found_bot = Bot(token)
            found_bot_data = await found_bot.get_me()
            try:
                await db.get_bot(token)  # TODO сделать список ботов после MVP
                await message.answer("Бот с таким токеном в системе уже найден.\n"
                                     "Введи другой токен или перейди в список ботов и поищи своего бота там")
            except Exception:
                bot_fullname, bot_username = found_bot_data.full_name, found_bot_data.username
                new_bot = DbBot(bot_token=token,
                                status="new",
                                created_at=datetime.utcnow(),
                                created_by=message.from_user.id,
                                settings={"start_msg": DefaultLocale.default_start_msg(),
                                          "web_app_button": DefaultLocale.open_web_app_button()},
                                locale=lang)

                working_directory = os.getcwd()
                copy_tree(f'{working_directory}/template', f'{working_directory}/bots/bot{token.replace(":", "___")}')
                logger.info(f'successfully create new sub bot files in directory bots/bot{token.replace(":", "___")}')
                with open(f'{working_directory}/bots/bot{token.replace(":", "___")}/.env', 'w') as envfile:
                    envfile.write(f"TELEGRAM_TOKEN={token}"
                                  f"\nDB_URL={config.DB_URL}"
                                  f"\nWEB_APP_URL={config.WEB_APP_URL}")
                logger.info(f'successfully .env sub bot file in directory bots/bot{token.replace(":", "___")}/.env')
                with open(f'{working_directory}/bots/bot{token.replace(":", "___")}/bot.service', 'r') as servicefile:
                    txt = servicefile.read().replace('{working_directory}', f'{working_directory}/bots/bot{token.replace(":", "___")}')
                with open(f'{working_directory}/bots/bot{token.replace(":", "___")}/bot.service', 'w') as servicefile:
                    servicefile.write(txt)

                await found_bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(text=DefaultLocale.open_web_app_button(),
                                                 web_app=WebAppInfo(url=config.WEB_APP_URL))
                )

                logger.debug("added web_app button to bot menu.")
                os.system(
                    f"echo {os.getenv('password')} | sudo -S cp {working_directory}/bots/bot{token.replace(':', '___')}/bot.service "
                    f"/etc/systemd/system/bot{token.replace(':', '___')}.service")
                os.system(f"echo {os.getenv('password')} | sudo -S systemctl daemon-reload")
                os.system(f"echo {os.getenv('password')} | sudo -S systemctl start bot{token.replace(':', '___')}.service")

                await db.add_bot(new_bot)

                await message.answer(
                    DefaultLocale.bot_will_initialize().format(bot_fullname, bot_username),
                    reply_markup=get_bot_menu_keyboard(WebAppInfo(url="https://zhilovhub.github.io/qwerty/"))
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


@router.message(States.BOT_MENU)
async def bot_menu_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    if message.photo and message.caption:
        photo_file_id = message.photo[-1].file_id
        params = message.caption.strip().split('\n')

        if len(params) != 2:
            return await message.answer("Чтобы добавить товар, прикрепи его картинку и отправь сообщение в виде:"
                                "\n\nНазвание\nЦена в рублях")
        if not params[-1].replace(',', '.').isdecimal():
            return await message.answer("Цена должна быть в формате: <b>100.00</b>")

        await bot.download(photo_file_id, destination=f"Files/img/{state_data['token']}__{params[0]}.jpg")
        with open(f"Files/img/{state_data['token']}__{params[0]}.jpg", 'rb') as photo_file:
            photo_bytes = photo_file.read()

        new_product = ProductWithoutId(bot_token=state_data['token'],
                                       name=params[0],
                                       description="",
                                       price=float(params[1]),
                                       picture=photo_bytes)
        await db_engine.get_product_db().add_product(new_product)
        await message.answer("Товар добавлен. Можно добавить ещё")

    else:
        match message.text:
            case "Стартовое сообщение":
                await message.answer("Пришли текст, который должен присылаться пользователям, "
                                     "когда они твоему боту отправляют /start", reply_markup=get_back_keyboard())
                await state.set_state(States.EDITING_START_MESSAGE)
                await state.set_data(state_data)
            case "Сообщение затычка":
                pass
            case "Посмотреть магазин":
                pass  # should be pass, it's nice
            case "Добавить товар":
                await message.reply("Чтобы добавить товар, прикрепи его картинку и отправь сообщение в виде:"
                                    "\n\nНазвание\nЦена в рублях")
            case "Запустить бота":
                pass
            case "Удалить бота":
                await message.answer("Бот удалится вместе со всей базой продуктов безвозвратно.\n"
                                     "Напиши ПОДТВЕРДИТЬ для подтверждения удаления", reply_markup=get_back_keyboard())
                await state.set_state(States.DELETE_BOT)
                await state.set_data(state_data)
            case _:
                await message.answer(
                    "Для навигации используй кнопки 👇",
                    reply_markup=get_bot_menu_keyboard(WebAppInfo(url="https://zhilovhub.github.io/qwerty/")))


@router.message(States.EDITING_START_MESSAGE)
async def editing_start_message_handler(message: Message, state: FSMContext):
    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращемся в меню...",
                reply_markup=get_bot_menu_keyboard(WebAppInfo(url="https://zhilovhub.github.io/qwerty/")))
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            bot = await db.get_bot(state_data["token"])
            if bot.settings:
                bot.settings["start_msg"] = message_text
                await db.update_bot(bot)

            await message.answer(
                "Стартовое сообщение изменено!",
                reply_markup=get_bot_menu_keyboard(WebAppInfo(url="https://zhilovhub.github.io/qwerty/")))
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@router.message(States.DELETE_BOT)
async def delete_bot_handler(message: Message, state: FSMContext):
    message_text = message.text
    state_data = await state.get_data()
    if message_text == "ПОДТВЕРДИТЬ":
            await db.del_bot(state_data["token"])

            await message.answer(
                "Бот удален",
                reply_markup=ReplyKeyboardRemove())
            await message.answer(DefaultLocale.input_token())
            await state.set_state(States.WAITING_FOR_TOKEN)
    elif message_text == "🔙 Назад":
            await message.answer(
                "Возвращемся в меню...",
                reply_markup=get_bot_menu_keyboard(WebAppInfo(url="https://zhilovhub.github.io/qwerty/")))
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
    else:
        await message.answer("Напиши ПОДТВЕРДИТЬ для подтверждения удаления или вернись назад")