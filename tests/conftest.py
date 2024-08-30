import asyncio

from aiogram import Bot
from aiogram.types import Chat

from common_utils.config import settings, database_settings
from common_utils.config.env_config import Mode

from database.models.models import Database, Base
from database.models.bot_model import BotDao, BotSchema
from database.models.user_model import UserDao
from database.models.option_model import OptionDao

from logs.config import test_logger

from tests.conftests import *  # noqa


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def check_example_and_test_env_files(event_loop):
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
async def user_db(database: Database) -> UserDao:
    user_db = database.get_user_dao()
    yield user_db
    await user_db.clear_table()


@pytest.fixture
async def bot_db(database: Database) -> BotDao:
    bot_db = database.get_bot_dao()
    yield bot_db
    await bot_db.clear_table()


@pytest.fixture
async def option_db(database: Database) -> OptionDao:
    option_db = database.get_option_dao()
    yield option_db
    await option_db.clear_table()


@pytest.fixture
async def payment_db(database: Database) -> PaymentDao:
    payment_db = database.get_payment_dao()
    yield payment_db
    await payment_db.clear_table()


@pytest.fixture
def tg_user() -> User:
    return User(id=6456011436, is_bot=False, first_name="Artem", username="test_user")


@pytest.fixture
def tg_chat() -> Chat:
    return Chat(id=6456011436, type="private")


@pytest.fixture
def subscribe_ended_user(user_schema: UserSchema) -> UserSchema:
    user_schema.subscribed_until = user_schema.registered_at + datetime.timedelta(days=31)
    user_schema.status = UserStatusValues.SUBSCRIPTION_ENDED
    return user_schema


@pytest.fixture
def subscribed_user(user_schema: UserSchema) -> UserSchema:
    user_schema.subscribed_until = datetime.datetime.now(tz=None) + datetime.timedelta(days=31)
    user_schema.status = UserStatusValues.SUBSCRIBED
    return user_schema


@pytest.fixture
async def add_subscribe_ended_user(subscribe_ended_user: UserSchema, user_db: UserDao) -> UserSchema:
    await user_db.add_user(subscribe_ended_user)
    return subscribe_ended_user


@pytest.fixture
async def add_subscribed_user(subscribed_user: UserSchema, user_db: UserDao) -> UserSchema:
    await user_db.add_user(subscribed_user)
    return subscribed_user


@pytest.fixture
async def add_option(option_schema: OptionSchema, option_db: OptionDao) -> OptionSchema:
    await option_db.add_option(option_schema)
    return option_schema


@pytest.fixture
async def tg_custom_bot() -> Bot:
    return Bot(token="7346456554:AAHGQOBfwJOtfLwYggVeoR2Qt-E6yEubOgo")


@pytest.fixture
def bot_schema(tg_user: User, tg_custom_bot: Bot, option_schema: OptionSchema) -> BotSchema:
    return BotSchema(
        bot_id=1,
        token=tg_custom_bot.token,
        status="online",
        created_at=datetime.datetime.now(),
        created_by=tg_user.id,
        options_id=option_schema.id,
        locale="default",
    )


@pytest.fixture
async def add_bot(bot_schema: BotSchema, bot_db: BotDao) -> BotSchema:
    await bot_db.add_bot(bot_schema)
    return bot_schema
