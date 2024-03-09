from aiogram.fsm.state import State, StatesGroup


# class InputToken(StatesGroup):
#     input = State()
#
#
# class AddProduct(StatesGroup):
#     input = State()

class States(StatesGroup):
    WAITING_FREE_TRIAL_APPROVE = State()
    WAITING_FOR_TOKEN = State()
    BOT_MENU = State()
    EDITING_START_MESSAGE = State()
    EDITING_DEFAULT_MESSAGE = State()
    DELETE_BOT = State()

