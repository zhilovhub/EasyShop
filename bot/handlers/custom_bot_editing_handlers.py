import re

from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from bot.main import bot, cache_resources_file_id_store
from bot.utils import MessageTexts
from bot.states.states import States
from bot.handlers.routers import custom_bot_editing_router
from bot.utils.send_instructions import send_instructions
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard, ReplyBackBotMenuKeyboard

from common_utils.keyboards.keyboards import InlineBotMenuKeyboard, InlineBotSettingsMenuKeyboard

from database.config import bot_db

from logs.config import logger


def is_valid_hex_code(string: str):
    regex = "^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"

    p = re.compile(regex)

    if string is None:
        return False

    if re.search(p, string):
        return True
    else:
        return False


@custom_bot_editing_router.message(States.EDITING_START_MESSAGE)
async def editing_start_message_handler(message: Message, state: FSMContext):
    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                if custom_bot.settings:
                    custom_bot.settings["start_msg"] = message_text
                else:
                    custom_bot.settings = {"start_msg": message_text}
                await bot_db.update_bot(custom_bot)

                await message.answer(
                    "Стартовое сообщение изменено!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id)
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

        match message_text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                if custom_bot.settings:
                    custom_bot.settings["default_msg"] = message_text
                else:
                    custom_bot.settings = {"default_msg": message_text}
                await bot_db.update_bot(custom_bot)

                await message.answer(
                    "Сообщение-затычка изменена!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Сообщение-затычка должна содержать текст")


@custom_bot_editing_router.message(States.EDITING_BG_COLOR)
async def editing_bg_color_handler(message: Message, state: FSMContext):
    message_text = message.text.strip()
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message_text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                if not is_valid_hex_code(message_text) and message_text != "telegram":
                    return await message.answer("Не получилось распознать ввод. Введите еще раз цвет в формате "
                                                "<i>#FFFFFF</i> или напишите <i>telegram</i> для дефолтных цветов.")

                bg_color = None if message_text == "telegram" else message_text

                if custom_bot.settings:
                    custom_bot.settings["bg_color"] = bg_color
                else:
                    custom_bot.settings = {"bg_color": bg_color}
                await bot_db.update_bot(custom_bot)

                await message.answer(
                    "Цвет фона изменен!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Цвет должен быть указан в тексте сообщения.")


@custom_bot_editing_router.message(States.EDITING_POST_ORDER_MESSAGE)
async def editing_post_order_message_handler(message: Message, state: FSMContext):
    message_text = message.html_text
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message_text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в главное меню...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                if custom_bot.settings:
                    custom_bot.settings["post_order_msg"] = message_text
                else:
                    custom_bot.settings = {"post_order_msg": message_text}
                await bot_db.update_bot(custom_bot)

                await message.answer(
                    "Сообщение после заказа изменено!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Сообщение должно содержать текст")


@custom_bot_editing_router.message(States.DELETE_BOT)
async def delete_bot_handler(message: Message, state: FSMContext):
    message_text = message.text
    state_data = await state.get_data()
    custom_bot = await bot_db.get_bot(state_data['bot_id'])

    match message_text:
        case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
            await message.answer(
                "Возвращаемся в главное меню...",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)

        case "ПОДТВЕРДИТЬ":
            logger.info(f"Disabling bot {state_data['bot_id']}, setting deleted status to db...")
            custom_bot.status = "Deleted"
            await bot_db.del_bot(custom_bot.bot_id)

            await message.answer(
                "Бот удален",
                reply_markup=ReplyKeyboardRemove()
            )
            await send_instructions(bot, None, message.from_user.id, cache_resources_file_id_store)
            await state.set_state(States.WAITING_FOR_TOKEN)
            await state.set_data({"bot_id": -1})

        case _:
            await message.answer("Напишите ПОДТВЕРДИТЬ для подтверждения удаления или вернитесь назад")
