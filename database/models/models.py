import os

from sqlalchemy.ext.asyncio import create_async_engine

from database.models.bot_model import BotDao
from database.models.user_model import UserDao
from database.models.order_model import OrderDao
from database.models.product_model import ProductDao
from database.models.custom_bot_user_model import CustomBotUserDao
from database.models.payment_model import PaymentDao
from database.models import Base

import logging.config
import logging

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
    def __init__(self, sqlalchemy_url: str) -> None:
        self.engine = create_async_engine(sqlalchemy_url, echo=bool(int(os.getenv("DEBUG"))))

        self.logger = logging.getLogger("db_logger")
        log_handler = logging.FileHandler(os.getenv("PROJECT_ROOT") + 'database/logs/all.log')
        log_formatter = logging.Formatter('[%(asctime)s][%(levelname)s] ::: %(filename)s(%(lineno)d) -> %(message)s')
        log_handler.setFormatter(log_formatter)
        if bool(int(os.getenv("DEBUG"))):
            self.logger.setLevel('DEBUG')
        else:
            self.logger.setLevel('INFO')
        self.logger.addHandler(log_handler)

        self.user_dao = UserDao(self.engine, self.logger)
        self.bot_dao = BotDao(self.engine, self.logger)
        self.product_dao = ProductDao(self.engine, self.logger)
        self.custom_bot_user_dao = CustomBotUserDao(self.engine, self.logger)
        self.order_dao = OrderDao(self.engine, self.logger)
        self.payment_dao = PaymentDao(self.engine, self.logger)

        self.logger.debug("New root database class initialized.", stack_info=True, stacklevel=2)

    async def connect(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.logger.debug("Table metadata created.")

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
