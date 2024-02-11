import datetime
import os
from distutils.dir_util import copy_tree
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot import config
from bot.main import bot, db, products_db
from bot.utils.database import DbUser
from aiogram.filters import Command
from bot.locales.misc import format_locales
from aiogram import Router, Bot, Dispatcher
from bot.filters.chat_type import ChatTypeFilter
from bot.keyboards import users as kb
from bot.states import states
from re import fullmatch
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.types import MenuButtonWebApp, WebAppInfo
from bot.config import logger
from bot.utils.database import DbBot
from magic_filter import F
from database.models.product_model import ProductWithoutId


router = Router(name="users_states")
router.message.filter(ChatTypeFilter(chat_type='private'))


@router.message(states.InputToken.input)
async def input_token_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.locale
    token = message.text
    if fullmatch(r"\d{10}:\w{35}", token):
        try:
            found_bot = Bot(token)
            found_bot_data = await found_bot.get_me()
            try:
                await db.get_bot(token)
                flag = True
                await message.answer("Bot already exists.")
            except:
                flag = False
            bot_fullname, bot_username = found_bot_data.full_name, found_bot_data.username
            await state.clear()
            new_bot = DbBot(bot_token=token,
                            status="new",
                            created_at=datetime.datetime.now(),
                            created_by=message.from_user.id,
                            settings={"start_msg": config.LOCALES[lang].default_start_msg,
                                      'web_app_button': config.LOCALES[lang].open_web_app_button},
                            locale=lang)

            working_directory = os.getcwd()
            copy_tree(f'{working_directory}/template', f'{working_directory}/bots/bot{token}')
            logger.info(f"successfully create new sub bot files in directory bots/bot{token}")
            with open(f'{working_directory}/bots/bot{token}/.env', 'w') as envfile:
                envfile.write(f"TELEGRAM_TOKEN={token}"
                              f"\nDB_URL={config.DB_URL}"
                              f"\nWEB_APP_URL={config.WEB_APP_URL}")
            logger.info(f"successfully .env sub bot file in directory bots/bot{token}/.env")
            with open(f'{working_directory}/bots/bot{token}/bot.service', 'r') as servicefile:
                txt = servicefile.read().replace('{working_directory}', f'{working_directory}/bots/bot{token}')
            with open(f'{working_directory}/bots/bot{token}/bot.service', 'w') as servicefile:
                servicefile.write(txt)
            await found_bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text=config.LOCALES[lang].open_web_app_button,
                                             web_app=WebAppInfo(url=config.WEB_APP_URL))
            )
            logger.debug("added web_app button to bot menu.")
            print(f"\n\n{os.getenv('PASSWORD')}\n\n")
            os.system(f"echo {os.getenv('PASSWORD')} | sudo -S -k cp {working_directory}/bots/bot{token}/bot.service /etc/systemd/system/bot{token}.service")
            os.system(f"echo {os.getenv('PASSWORD')} | sudo -S -k systemctl daemon-reload")
            os.system(f"echo {os.getenv('PASSWORD')} | sudo -S -k systemctl start bot{token}.service")
            if not flag:
                await db.add_bot(new_bot)
            await message.answer(
                config.LOCALES[lang].bot_will_initialize.format(bot_fullname, bot_username),
                reply_markup=kb.create_back_to_main_menu_keyboard(lang)
            )
        except TelegramUnauthorizedError:
            await message.answer(config.LOCALES[lang].bot_with_token_not_found)
        except Exception:
            logger.error(f"Error while adding new bot wit token {token} from user {message.from_user.id}", exc_info=True)
            await message.answer("Unknown error while adding bot")
    else:
        await message.answer(config.LOCALES[lang].incorrect_bot_token)


@router.message(states.AddProduct.input, F.photo)
async def input_product_photo_handler(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    params = message.caption.strip().split('\n')
    data = await state.get_data()
    if len(params) != 3:
        return await message.reply("Необходимо отправить фото товара с подписью в формате:"
                                   "\n\nНазвание\nОписание\nЦена в рублях")
    if not params[-1].replace(',', '.').isdecimal():
        return await message.reply("Цена должна быть в формате: <b>100.00</b>")
    await bot.download(photo_file_id, destination=f"Files/img/{data['token']}__{params[0]}.jpg")
    await state.update_data({"file_id": photo_file_id, 'file_path': f"Files/img/{data['token']}__{params[0]}.jpg"})
    with open(f"Files/img/{data['token']}__{params[0]}.jpg", 'rb') as photo_file:
        photo_bytes = photo_file.read()
    new_product = ProductWithoutId(bot_token=data['token'],
                                   name=params[0],
                                   description=params[1],
                                   price=float(params[2]),
                                   picture=photo_bytes)
    await products_db.add_product(new_product)
    await message.reply("Товар добавлен, отправь еще один или введи /finish для завершения.")


@router.message(states.AddProduct.input, Command(commands=['finish'], prefix='!/'))
async def input_product_finish_handler(message: Message, state: FSMContext):
    await state.clear()
    return await message.answer("Добавление товаров завершено.")


@router.message(states.AddProduct.input)
async def input_product_handler(message: Message, state: FSMContext):
    return await message.reply("Необходимо отправить фото товара с подписью в формате:"
                               "\n\nНазвание\nОписание\nЦена в рублях")
