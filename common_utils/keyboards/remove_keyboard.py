from typing import ClassVar

from aiogram.types import ReplyKeyboardRemove


class OurReplyKeyboardRemove(ReplyKeyboardRemove):
    """The keyboard used instead of ReplyKeyboardRemove. It allows to check whether it triggered during tests"""

    has_been_triggered: ClassVar[bool] = False

    def __init__(self) -> None:
        super().__init__()
        OurReplyKeyboardRemove.has_been_triggered = True
