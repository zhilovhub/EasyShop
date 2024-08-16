from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.exceptions import TelegramBadRequest

from bot.utils import MessageTexts
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard

from common_utils.config import common_settings
from common_utils.cache_json.cache_json import JsonStore

from logs.config import logger


async def send_instructions(
    bot: Bot, custom_bot_id: int | None, chat_id: int, cache_resources_file_id_store: JsonStore
) -> None:
    """Sends instruction and considers whether user has bots or not. Usually is called from /start"""
    file_ids = cache_resources_file_id_store.get_data()
    file_name = "start_instruction.png"

    bot_father_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔐 Получить токен", url="t.me/BotFather"),
                InlineKeyboardButton(text="🔎 Инструкция", url="https://ezshoptg.tilda.ws/"),
            ],
            [InlineKeyboardButton(text="🤝 Реферальная система", callback_data="ref_start")],
            [InlineKeyboardButton(text="🔮 Подписаться на канал", url="t.me/EzShopOfficial")],
        ]
    )

    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=file_ids[file_name],
            caption=MessageTexts.INSTRUCTION_MESSAGE.value,
            reply_markup=bot_father_keyboard,
        )
        if custom_bot_id:
            await bot.send_message(
                chat_id=chat_id, text="✅ У Вас уже есть бот", reply_markup=ReplyBotMenuKeyboard.get_keyboard()
            )
        else:
            await bot.send_message(
                chat_id=chat_id, text="❌ Вы всё ещё не создали бота", reply_markup=ReplyKeyboardRemove()
            )
    except (TelegramBadRequest, KeyError) as e:
        logger.info(f"error while sending instructions.... cache is empty, sending raw files {e}")
        instruction_message = await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(common_settings.RESOURCES_PATH.format(file_name)),
            caption=MessageTexts.INSTRUCTION_MESSAGE.value,
            reply_markup=bot_father_keyboard,
        )
        file_ids[file_name] = instruction_message.photo[-1].file_id
        cache_resources_file_id_store.update_data(file_ids)
