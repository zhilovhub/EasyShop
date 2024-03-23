import asyncio
import os
import sys

import pytest
from dotenv import load_dotenv

from database.models.bot_model import BotDao
from database.models.models import Base
from database.models.models import Database
from database.models.order_model import OrderDao
from database.models.payment_model import PaymentDao
from database.models.product_model import ProductDao
from database.models.user_model import UserDao
from stoke.stoke import Stoke
from subscription.scheduler import Scheduler
from subscription.subscription import Subscription
from tests.schemas import bot_schema_without_id_1, bot_schema_without_id_2, user_schema_1, user_schema_2

load_dotenv()


@pytest.fixture
async def database() -> Database:
    database = Database(sqlalchemy_url=os.environ["DB_FOR_TESTS"])
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await database.connect()
    yield database
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def stoke(database: Database) -> Stoke:
    stoke = Stoke(database)
    return stoke


@pytest.fixture
async def subscription(database: Database) -> Subscription:
    _scheduler = Scheduler(os.getenv("SCHEDULER_FOR_TESTS"), "postgres", "Europe/Moscow")
    subscription = Subscription(database, _scheduler)
    await _scheduler.start()
    yield subscription
    await _scheduler.stop_scheduler()


@pytest.fixture
def user_db(database: Database) -> UserDao:
    return database.get_user_dao()


@pytest.fixture
def bot_db(database: Database) -> BotDao:
    return database.get_bot_dao()


@pytest.fixture
def product_db(database: Database) -> ProductDao:
    return database.get_product_db()


@pytest.fixture
def order_db(database: Database) -> OrderDao:
    return database.get_order_dao()


@pytest.fixture
def payment_db(database: Database) -> PaymentDao:
    return database.get_payment_dao()


@pytest.fixture
async def before_add_user(user_db: UserDao) -> None:
    await user_db.add_user(user_schema_1)


@pytest.fixture
async def before_add_two_users(user_db: UserDao) -> None:
    await user_db.add_user(user_schema_1)
    await user_db.add_user(user_schema_2)


@pytest.fixture
async def before_add_bot(bot_db: BotDao, before_add_two_users) -> None:
    await bot_db.add_bot(bot_schema_without_id_1)


@pytest.fixture
async def before_add_two_bots(bot_db: BotDao, before_add_two_users) -> None:
    await bot_db.add_bot(bot_schema_without_id_1)
    await bot_db.add_bot(bot_schema_without_id_2)


@pytest.fixture(scope="session")
def event_loop():
    """
    Creates an instance of the default event loop for the test session.
    """
    if sys.platform.startswith("win") and sys.version_info[:2] >= (3, 8):
        # Avoid "RuntimeError: Event loop is closed" on Windows when tearing down tests
        # https://github.com/encode/httpx/issues/914
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
