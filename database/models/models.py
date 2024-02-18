import os

from sqlalchemy.ext.asyncio import create_async_engine

from database.models import Base
from database.models.bot_model import BotDao
from database.models.user_model import UserDao
from database.models.order_model import OrderDao
from database.models.product_model import ProductDao
from database.models.custom_bot_user_model import CustomBotUserDao

from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self, sqlalchemy_url: str) -> None:
        self.engine = create_async_engine(sqlalchemy_url, echo=bool(int(os.getenv("DEBUG"))))
        self.user_dao = UserDao(self.engine)
        self.bot_dao = BotDao(self.engine)
        self.product_dao = ProductDao(self.engine)
        self.custom_bot_user_dao = CustomBotUserDao(self.engine)
        self.order_dao = OrderDao(self.engine)

    async def connect(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

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
