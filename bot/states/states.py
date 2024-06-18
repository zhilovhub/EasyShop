from aiogram.fsm.state import State, StatesGroup


# class InputToken(StatesGroup):
#     input = State()
#
#
# class AddProduct(StatesGroup):
#     input = State()

class States(StatesGroup):
    WAITING_FREE_TRIAL_APPROVE = State()

    WAITING_PAYMENT_PAY = State()
    WAITING_PAYMENT_APPROVE = State()
    SUBSCRIBE_ENDED = State()

    WAITING_FOR_TOKEN = State()
    BOT_MENU = State()
    EDITING_START_MESSAGE = State()
    EDITING_DEFAULT_MESSAGE = State()
    DELETE_BOT = State()

    EDITING_COMPETITION_NAME = State()
    EDITING_COMPETITION_DESCRIPTION = State()
    EDITING_COMPETITION_MEDIA_FILES = State()

    EDITING_MAILING_MESSAGE = State()
    EDITING_MAILING_BUTTON_TEXT = State()
    EDITING_MAILING_BUTTON_URL = State()
    EDITING_MAILING_MEDIA_FILES = State()
    EDITING_DELAY_DATE = State()

    EDITING_POST_TEXT = State()
    EDITING_POST_BUTTON_TEXT = State()
    EDITING_POST_BUTTON_URL = State()
    EDITING_POST_MEDIA_FILES = State()
    EDITING_POST_DELAY_DATE = State()

    EDITING_COMPETITION_END_DATE = State()
