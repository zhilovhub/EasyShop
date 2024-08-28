import datetime

import pytest

from aiogram import Dispatcher, Bot
from aiogram.types import User, Chat

from bot.main import bot, storage, dp, include_routers, setup_storage_and_schedulers, scheduler

from common_utils.storage.storage import AlchemyStorageAsync

from database.models.user_model import UserSchema, UserStatusValues, UserDao


@pytest.fixture(scope="class")
async def dispatcher() -> Dispatcher:
    await setup_storage_and_schedulers()
    include_routers()
    return dp  # Используем реальный instance диспатчера из main.py, чтобы проверить боевые условия


@pytest.fixture(autouse=True)
async def clear_scheduler() -> None:
    yield
    scheduler.clear_table()


@pytest.fixture
async def main_storage() -> AlchemyStorageAsync:
    yield storage  # Используем реальный instance storage из main.py, чтобы проверить боевые условия
    await storage.clear_table()


@pytest.fixture
def tg_main_bot() -> Bot:
    return bot  # Используем реальный instance бота из main.py, чтобы проверить боевые условия


@pytest.fixture
def tg_user() -> User:
    return User(id=6456011436, is_bot=False, first_name="Artem", username="test_user")


@pytest.fixture
def tg_chat() -> Chat:
    return Chat(id=6456011436, type="private")


@pytest.fixture
def user_schema(tg_user: User) -> UserSchema:
    return UserSchema(
        user_id=tg_user.id,
        username=tg_user.username,
        status=UserStatusValues.NEW,
        subscribed_until=None,
        registered_at=datetime.date(1960, 12, 12),
    )


@pytest.fixture
def subscribe_ended_user(user_schema: UserSchema) -> UserSchema:
    user_schema.subscribed_until = user_schema.registered_at + datetime.timedelta(days=31)
    user_schema.status = UserStatusValues.SUBSCRIPTION_ENDED
    return user_schema


@pytest.fixture
async def add_subscribe_ended_user(subscribe_ended_user: UserSchema, user_db: UserDao) -> UserSchema:
    await user_db.add_user(subscribe_ended_user)
    return subscribe_ended_user
