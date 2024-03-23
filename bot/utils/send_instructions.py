from aiogram import Bot
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest

from bot import config
from bot.utils import JsonStore, MessageTexts


async def send_instructions(bot: Bot, chat_id: int, cache_resources_file_id_store: JsonStore) -> None:
    file_ids = cache_resources_file_id_store.get_data()
    try:
        await bot.send_video(
            chat_id=chat_id,
            video=file_ids["botfather.mp4"],
            caption=MessageTexts.INSTRUCTION_MESSAGE.value
        )
    except (TelegramBadRequest, KeyError) as e:
        config.logger.info(f"error while sending instructions.... cache is empty, sending raw files {e}")
        video_message = await bot.send_video(
            chat_id=chat_id,
            video=FSInputFile(config.RESOURCES_PATH.format("botfather.mp4")),
            caption=MessageTexts.INSTRUCTION_MESSAGE.value
        )
        file_ids[f"botfather.mp4"] = video_message.video.file_id
        cache_resources_file_id_store.update_data(file_ids)
