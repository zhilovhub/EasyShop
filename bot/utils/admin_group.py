from aiogram.types import Message

from bot.main import bot, config, logger


async def send_event(message: Message) -> None:
    try:
        await bot.send_message(
            chat_id=config.ADMIN_GROUP_ID,
            text=message.text
        )
    except Exception as e:
        logger.info(e)
