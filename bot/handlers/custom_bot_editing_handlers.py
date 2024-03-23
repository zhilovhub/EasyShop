from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.main import bot_db, product_db
from bot.config import logger
from bot.keyboards import *
from bot.states.states import States
from bot.handlers.routers import custom_bot_editing_router


@custom_bot_editing_router.message(States.EDITING_START_MESSAGE)
async def editing_start_message_handler(message: Message, state: FSMContext):
    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        user_bot = await bot_db.get_bot(state_data['bot_id'])
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"], user_bot.status)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            user_bot = await bot_db.get_bot(state_data["bot_id"])
            if user_bot.settings:
                user_bot.settings["start_msg"] = message_text
            else:
                user_bot.settings = {"start_msg": message_text}
            await bot_db.update_bot(user_bot)

            await message.answer(
                "Стартовое сообщение изменено!",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"], user_bot.status)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.EDITING_DEFAULT_MESSAGE)
async def editing_default_message_handler(message: Message, state: FSMContext):
    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        user_bot = await bot_db.get_bot(state_data['bot_id'])
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"], user_bot.status)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            user_bot = await bot_db.get_bot(state_data["bot_id"])
            if user_bot.settings:
                user_bot.settings["default_msg"] = message_text
            else:
                user_bot.settings = {"default_msg": message_text}
            await bot_db.update_bot(user_bot)

            await message.answer(
                "Сообщение-затычка изменена!",
                reply_markup=get_bot_menu_keyboard(state_data["bot_id"], user_bot.status)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
    else:
        await message.answer("Сообщение-затычка должна содержать текст")


@custom_bot_editing_router.message(States.DELETE_BOT)
async def delete_bot_handler(message: Message, state: FSMContext):
    message_text = message.text
    state_data = await state.get_data()
    user_bot = await bot_db.get_bot(state_data['bot_id'])
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
            reply_markup=get_bot_menu_keyboard(state_data["bot_id"], user_bot.status)
        )
        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer("Напишите ПОДТВЕРДИТЬ для подтверждения удаления или вернитесь назад")


@custom_bot_editing_router.callback_query(lambda q: q.data.startswith('product:delete'))
async def delete_product_handler(query: CallbackQuery):
    product_id = int(query.data.split("_")[-1])
    await product_db.delete_product(product_id)
    await query.message.delete()
