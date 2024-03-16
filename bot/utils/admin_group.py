import os

from aiogram.types import Message

from bot.main import bot, config


async def send_event(message: Message) -> None:
    await bot.send_message(
        chat_id=config.ADMIN_GROUP_ID,
        text=message.text
    )
