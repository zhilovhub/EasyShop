import pytest

from common_utils.config import database_settings

from database.models.models import Database, Base

from logs.config import test_logger


@pytest.fixture(scope="session", autouse=True)
async def init_and_drop_database(check_test_env):  # noqa
    database = Database(sqlalchemy_url=database_settings.SQLALCHEMY_URL, logger=test_logger, is_test_mode=True)

    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await database.connect()

    yield

    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture
def database():
    return Database(sqlalchemy_url=database_settings.SQLALCHEMY_URL, logger=test_logger, is_test_mode=True)
