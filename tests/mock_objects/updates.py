import datetime

from aiogram import Bot
from aiogram.types import Message, Chat, User


class MockMessage(Message):
    def __init__(self, bot: Bot, chat: Chat, from_user: User, text: str) -> None:
        super().__init__(
            message_id=1,
            date=datetime.datetime.now(),
            chat=chat,
            from_user=from_user,
            text=text,
        )
        self.as_(bot)
