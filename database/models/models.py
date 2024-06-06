import os

from sqlalchemy.ext.asyncio import create_async_engine

from database.models.bot_model import BotDao
from database.models.user_model import UserDao
from database.models.order_model import OrderDao
from database.models.product_model import ProductDao
from database.models.mailing_model import MailingDao
from database.models.channel_model import ChannelDao
from database.models.payment_model import PaymentDao
from database.models.category_model import CategoryDao
from database.models.randomizer_model import RandomizerDao
from database.models.competition_model import CompetitionDao
from database.models.mailing_media_files import MailingMediaFileDao
from database.models.custom_bot_user_model import CustomBotUserDao
from database.models import Base
from database.models.competition_media_files_model import CompetitionMediaFileDao

from dotenv import load_dotenv

load_dotenv()


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


@singleton
class Database:
    def __init__(self, sqlalchemy_url: str, logger) -> None:
        self.engine = create_async_engine(sqlalchemy_url)
        self.logger = logger

        self.user_dao = UserDao(self.engine, self.logger)
        self.bot_dao = BotDao(self.engine, self.logger)
        self.product_dao = ProductDao(self.engine, self.logger)
        self.custom_bot_user_dao = CustomBotUserDao(self.engine, self.logger)
        self.order_dao = OrderDao(self.engine, self.logger)
        self.payment_dao = PaymentDao(self.engine, self.logger)
        self.category_dao = CategoryDao(self.engine, self.logger)
        self.competition_dao = CompetitionDao(self.engine, self.logger)
        self.competition_media_file_dao = CompetitionMediaFileDao(
            self.engine, self.logger)
        self.mailing_dao = MailingDao(self.engine, self.logger)
        self.mailing_media_file_dao = MailingMediaFileDao(
            self.engine, self.logger)
        self.randomizer_dao = RandomizerDao(self.engine, self.logger)
        self.channel_dao = ChannelDao(self.engine, self.logger)

        self.logger.debug("Database class is initialized")

    async def connect(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.logger.debug("Metadata is used to create Tables")

    def get_user_dao(self) -> UserDao:
        return self.user_dao

    def get_bot_dao(self) -> BotDao:
        return self.bot_dao

    def get_product_db(self) -> ProductDao:
        return self.product_dao

    def get_custom_bot_user_db(self) -> CustomBotUserDao:
        return self.custom_bot_user_dao

    def get_order_dao(self) -> OrderDao:
        return self.order_dao

    def get_payment_dao(self) -> PaymentDao:
        return self.payment_dao

    def get_category_dao(self) -> CategoryDao:
        return self.category_dao

    def get_competition_dao(self) -> CompetitionDao:
        return self.competition_dao

    def get_competition_media_file_dao(self) -> CompetitionMediaFileDao:
        return self.competition_media_file_dao

    def get_mailing_dao(self) -> MailingDao:
        return self.mailing_dao

    def get_mailing_media_file_dao(self) -> MailingMediaFileDao:
        return self.mailing_media_file_dao

    def get_randomizer_dao(self) -> RandomizerDao:
        return self.randomizer_dao

    def get_channel_dao(self) -> ChannelDao:
        return self.channel_dao
