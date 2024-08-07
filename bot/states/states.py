from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    """Describes the possible states of the main bot users"""

    WAITING_PAYMENT_PAY = State()
    WAITING_PAYMENT_APPROVE = State()
    SUBSCRIBE_ENDED = State()

    WAITING_FOR_TOKEN = State()
    BOT_MENU = State()
    EDITING_START_MESSAGE = State()
    EDITING_DEFAULT_MESSAGE = State()
    EDITING_POST_ORDER_MESSAGE = State()
    EDITING_BG_COLOR = State()
    DELETE_BOT = State()

    EDITING_POST_TEXT = State()
    EDITING_POST_BUTTON_TEXT = State()
    EDITING_POST_BUTTON_URL = State()
    EDITING_POST_MEDIA_FILES = State()
    EDITING_POST_DELAY_DATE = State()

    EDITING_CONTEST_WINNERS_COUNT = State()
    EDITING_CONTEST_FINISH_DATE = State()

    IMPORT_PRODUCTS = State()

    GOODS_COUNT_MANAGE = State()

    WAITING_FOR_NEW_ORDER_OPTION_TEXT = State()
    WAITING_FOR_ORDER_OPTION_EMOJI = State()
    WAITING_FOR_ORDER_OPTION_TEXT = State()
    WAITING_FOR_ORDER_OPTION_POSITION = State()

    WAITING_FOR_NEW_ORDER_CHOOSE_OPTION_TEXT = State()
    WAITING_FOR_ORDER_CHOOSE_OPTION_TEXT = State()
