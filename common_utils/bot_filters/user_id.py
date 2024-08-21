from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter


class UserIdFilter(BaseFilter):
    """The filter that checks if written user in provided id list"""

    def __init__(self, user_id: int | list[int]):
        """
        :param user_id: available chat ids
        """
        if isinstance(user_id, int):
            self.user_id = [user_id]
        else:
            self.user_id = user_id

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return event.from_user.id in self.user_id
