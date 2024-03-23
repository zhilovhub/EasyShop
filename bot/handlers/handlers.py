from datetime import datetime, timedelta

from typing import *

from aiogram import Router, Bot, BaseMiddleware
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, CallbackQuery, ContentType, User
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest
from aiogram.fsm.context import FSMContext, StorageKey
from aiogram.utils.token import TokenValidationError, validate_token

from aiohttp.client_exceptions import ClientConnectorError

from bot import config
from bot.main import bot, dp, subscription
from bot.utils import JsonStore
from bot.config import logger
from bot.keyboards import *
from bot.handlers.routers import user_db, bot_db, product_db, order_db, pay_db
from bot.states.states import States
from bot.utils.admin_group import send_event, success_event, EventTypes
from bot.utils.custom_bot_launching import start_custom_bot, stop_custom_bot
from bot.filters.chat_type import ChatTypeFilter
from bot.exceptions.exceptions import *

from database.models.bot_model import BotSchemaWithoutId
from database.models.user_model import UserSchema, UserStatusValues
from database.models.order_model import OrderNotFound, OrderStatusValues

from magic_filter import F

from subscription.subscription import UserHasAlreadyStartedTrial


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


@router.message(States.WAITING_FOR_TOKEN)
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
        reply_markup=get_bot_menu_keyboard(bot_id, user_bot.status)
    )
    await state.set_state(States.BOT_MENU)
    await state.set_data({"bot_id": bot_id})



