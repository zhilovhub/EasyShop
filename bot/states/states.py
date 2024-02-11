from aiogram.fsm.state import State, StatesGroup


class InputToken(StatesGroup):
    input = State()


class AddProduct(StatesGroup):
    input = State()
