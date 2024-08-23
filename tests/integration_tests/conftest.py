import pytest

from aiogram import Dispatcher, Bot
from aiogram.types import User, Chat

from bot.main import bot, storage, dp, include_routers, setup_storage_and_schedulers

from common_utils.storage.storage import AlchemyStorageAsync


@pytest.fixture
async def dispatcher() -> Dispatcher:
    await setup_storage_and_schedulers()
    include_routers()
    return dp  # Используем реальный instance диспатчера из main.py, чтобы проверить боевые условия


@pytest.fixture
def main_storage() -> AlchemyStorageAsync:
    return storage  # Используем реальный instance storage из main.py, чтобы проверить боевые условия


@pytest.fixture
def tg_main_bot() -> Bot:
    return bot  # Используем реальный instance бота из main.py, чтобы проверить боевые условия


@pytest.fixture
def tg_user() -> User:
    return User(
        id=6456011436,
        is_bot=False,
        first_name="Artem",
    )


@pytest.fixture
def tg_chat() -> Chat:
    return Chat(id=6456011436, type="private")
