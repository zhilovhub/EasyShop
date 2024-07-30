import pytest

from database.models.models import Database, Base
from common_utils.env_config import SQLALCHEMY_URL

from logs.config import test_logger


@pytest.fixture(scope="session", autouse=True)
async def init_and_drop_database():
    database = Database(sqlalchemy_url=SQLALCHEMY_URL, logger=test_logger)

    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await database.connect()

    yield

    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
