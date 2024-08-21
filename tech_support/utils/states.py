from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """Describes the possible states of the support bot users"""

    SEND_SUGGESTION_TO_ADMIN = State()
    SEND_QUESTION_TO_ADMINS = State()


class AdminStates(StatesGroup):
    """Describes the possible states of the support bot admins"""

    ANSWER_MESSAGE_TO_USER = State()
