from aiogram import Bot
from aiogram.types import FSInputFile, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from bot import config
from bot.utils import JsonStore, MessageTexts
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard

from logs.config import logger


async def send_instructions(
        bot: Bot,
        custom_bot_id: int | None,
        chat_id: int,
        cache_resources_file_id_store: JsonStore
) -> None:
    file_ids = cache_resources_file_id_store.get_data()
    file_name = "start_instruction.png"

    bot_father_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔐 Получить токен",
                    url="t.me/BotFather"
                )
            ]
        ]
    )

    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=file_ids[file_name],
            caption=MessageTexts.INSTRUCTION_MESSAGE.value,
            reply_markup=bot_father_keyboard
        )
        if custom_bot_id:
            await bot.send_message(
                chat_id=chat_id,
                text="✅ У Вас уже есть бот",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=custom_bot_id)
            )
    except (TelegramBadRequest, KeyError) as e:
        logger.info(f"error while sending instructions.... cache is empty, sending raw files {e}")
        instruction_message = await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(config.RESOURCES_PATH.format(file_name)),
            caption=MessageTexts.INSTRUCTION_MESSAGE.value,
            reply_markup=bot_father_keyboard
        )
        file_ids[file_name] = instruction_message.photo[-1].file_id
        cache_resources_file_id_store.update_data(file_ids)
