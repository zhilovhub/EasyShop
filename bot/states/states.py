from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    WAITING_FOR_TOKEN = State()
    BOT_MENU = State()
    EDITING_START_MESSAGE = State()
    EDITING_DEFAULT_MESSAGE = State()
    DELETE_BOT = State()
