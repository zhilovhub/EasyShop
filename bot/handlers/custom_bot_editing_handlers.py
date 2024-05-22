from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.main import bot_db, product_db, bot, cache_resources_file_id_store
from bot.config import logger
from bot.keyboards import *
from bot.states.states import States
from bot.handlers.routers import custom_bot_editing_router
from bot.utils.send_instructions import send_instructions


@custom_bot_editing_router.message(States.EDITING_START_MESSAGE)
async def editing_start_message_handler(message: Message, state: FSMContext):
    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в главное меню...",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            if custom_bot.settings:
                custom_bot.settings["start_msg"] = message_text
            else:
                custom_bot.settings = {"start_msg": message_text}
            await bot_db.update_bot(custom_bot)

            await message.answer(
                "Стартовое сообщение изменено!",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
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
        custom_bot = await bot_db.get_bot(state_data['bot_id'])
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в главное меню...",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            if custom_bot.settings:
                custom_bot.settings["default_msg"] = message_text
            else:
                custom_bot.settings = {"default_msg": message_text}
            await bot_db.update_bot(custom_bot)

            await message.answer(
                "Сообщение-затычка изменена!",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
    else:
        await message.answer("Сообщение-затычка должна содержать текст")


@custom_bot_editing_router.message(States.DELETE_BOT)
async def delete_bot_handler(message: Message, state: FSMContext):
    message_text = message.text
    state_data = await state.get_data()
    custom_bot = await bot_db.get_bot(state_data['bot_id'])
    if message_text == "ПОДТВЕРДИТЬ":
        logger.info(f"Disabling bot {state_data['bot_id']}, setting deleted status to db...")
        custom_bot.status = "Deleted"
        await bot_db.del_bot(custom_bot.bot_id)

        await message.answer(
            "Бот удален",
            reply_markup=ReplyKeyboardRemove()
        )
        await send_instructions(bot, None, message.from_user.id, cache_resources_file_id_store)
        await state.set_state(States.WAITING_FOR_TOKEN)
    elif message_text == "🔙 Назад":
        await message.answer(
            "Возвращаемся в главное меню...",
            reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
        )
        await message.answer(
            MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
            reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
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
