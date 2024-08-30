import pytest

from aiogram import Dispatcher, Bot

from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard
from bot.main import bot, storage, dp, include_routers, setup_storage_and_schedulers, scheduler
from common_utils.keyboards.remove_keyboard import OurReplyKeyboardRemove

from common_utils.storage.storage import AlchemyStorageAsync


@pytest.fixture(scope="class")
async def dispatcher() -> Dispatcher:
    await setup_storage_and_schedulers()
    include_routers()
    return dp  # Используем реальный instance диспатчера из main.py, чтобы проверить боевые условия


@pytest.fixture(autouse=True)
async def clear_scheduler() -> None:
    yield
    scheduler.clear_table()


@pytest.fixture(autouse=True)
async def clear_keyboards_triggers() -> None:
    for keyboard in (ReplyBotMenuKeyboard, OurReplyKeyboardRemove):
        keyboard.has_been_triggered = False


@pytest.fixture
async def main_storage() -> AlchemyStorageAsync:
    yield storage  # Используем реальный instance storage из main.py, чтобы проверить боевые условия
    await storage.clear_table()


@pytest.fixture
def tg_main_bot() -> Bot:
    return bot  # Используем реальный instance бота из main.py, чтобы проверить боевые условия
