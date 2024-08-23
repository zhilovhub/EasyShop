import pytest

from common_utils.config import settings, database_settings
from common_utils.config.env_config import Mode

from database.models.models import Database, Base
from database.models.user_model import UserDao

from logs.config import test_logger


@pytest.fixture(scope="session")
def check_example_and_test_env_files():
    """Checks that .env-example equals to .test.env"""
    with open(
            ".env-example", "r", encoding="utf-8"  # fmt: skip
    ) as env_example_f, open(".test.env", "r", encoding="utf-8") as env_test_f:  # fmt: skip
        converter = lambda file: [line.strip().split("=")[0] for line in file.readlines()]  # noqa

        example_variables = converter(env_example_f)
        test_variables = converter(env_test_f)

    assert example_variables == test_variables


@pytest.fixture(scope="session")
async def check_where_env_is_test(check_example_and_test_env_files):
    assert settings.MODE == Mode.TEST


@pytest.fixture(scope="session", autouse=True)
async def init_and_drop_database(check_where_env_is_test):  # noqa
    database = Database(sqlalchemy_url=database_settings.SQLALCHEMY_URL, logger=test_logger)

    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await database.connect()

    yield

    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture
def database():
    return Database(sqlalchemy_url=database_settings.SQLALCHEMY_URL, logger=test_logger)


@pytest.fixture
def user_db(database: Database) -> UserDao:
    return database.get_user_dao()
