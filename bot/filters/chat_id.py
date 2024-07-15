from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter


class ChatId(BaseFilter):
    def __init__(self, chat_id: int | list[int]):
        self.chat_id = chat_id

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        _id = event.chat.id if isinstance(event, Message) else event.message.chat.id
        if isinstance(_id, list):
            return _id in self.chat_id
        return _id == self.chat_id
