import json
import os
import string
from random import sample
from magic_filter import F

from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.main import bot, db_engine
from bot.config import logger
from bot.keyboards import *
from bot.states.states import States
from bot.handlers.routers import admin_bot_menu_router
from bot.utils.custom_bot_launching import start_custom_bot, stop_custom_bot

from database.models.order_model import OrderSchema
from database.models.product_model import ProductWithoutId

product_db = db_engine.get_product_db()
bot_db = db_engine.get_bot_dao()


@admin_bot_menu_router.message(States.BOT_MENU, F.photo)
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


@admin_bot_menu_router.message(States.BOT_MENU)
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


@admin_bot_menu_router.message(F.web_app_data)
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
