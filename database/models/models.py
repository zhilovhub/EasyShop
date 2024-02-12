from sqlalchemy.ext.asyncio import create_async_engine

from database.models.user_model import UserDao
from database.models.product_model import ProductDao
from database.models.custom_bot_user_model import CustomBotUserDao
from database.models.order_model import OrderDao


class Database:
    def __init__(self, sqlalchemy_url: str) -> None:
        self.engine = create_async_engine(sqlalchemy_url)
        self.user_dao = UserDao(self.engine)
        self.product_dao = ProductDao(self.engine)
        self.custom_bot_user_dao = CustomBotUserDao(self.engine)
        self.order_dao = OrderDao(self.engine)

    def get_user_dao(self) -> UserDao:
        return self.user_dao

    def get_product_db(self) -> ProductDao:
        return self.product_dao

    def get_custom_bot_user_db(self) -> CustomBotUserDao:
        return self.custom_bot_user_dao

    def get_order_dao(self) -> OrderDao:
        return self.order_dao
