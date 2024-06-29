from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    WAITING_PAYMENT_PAY = State()
    WAITING_PAYMENT_APPROVE = State()
    SUBSCRIBE_ENDED = State()

    WAITING_FOR_TOKEN = State()
    BOT_MENU = State()
    EDITING_START_MESSAGE = State()
    EDITING_DEFAULT_MESSAGE = State()
    DELETE_BOT = State()

    EDITING_POST_TEXT = State()
    EDITING_POST_BUTTON_TEXT = State()
    EDITING_POST_BUTTON_URL = State()
    EDITING_POST_MEDIA_FILES = State()
    EDITING_POST_DELAY_DATE = State()

    IMPORT_PRODUCTS = State()

    GOODS_COUNT_MANAGE = State()
