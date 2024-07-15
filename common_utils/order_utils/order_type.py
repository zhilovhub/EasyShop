from enum import Enum


class OrderType(Enum):
    MAIN_BOT_TEST_ORDER = 1
    CUSTOM_BOT_ORDER = 2


class UnknownOrderType(Exception):
    def __init__(self, message):
        super().__init__(message)
