import asyncio
import os
import sys

from dotenv import load_dotenv

import pytest

from database.models.models import Database
from database.models.bot_model import BotDao
from database.models.user_model import UserDao
from database.models.product_model import ProductDao

from database.models.models import Base

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
def user_db(database: Database) -> UserDao:
    return database.get_user_dao()


@pytest.fixture
def bot_db(database: Database) -> BotDao:
    return database.get_bot_dao()


@pytest.fixture
def product_db(database: Database) -> ProductDao:
    return database.get_product_db()


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
