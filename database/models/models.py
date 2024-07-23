from sqlalchemy.ext.asyncio import create_async_engine

from database.models.bot_model import BotDao
from database.models.adv_model import AdvDao
from database.models.user_model import UserDao
from database.models.order_model import OrderDao
from database.models.product_model import ProductDao
from database.models.channel_model import ChannelDao
from database.models.payment_model import PaymentDao
from database.models.mailing_model import MailingDao
from database.models.contest_model import ContestDao
from database.models.category_model import CategoryDao
from database.models.user_role_model import UserRoleDao
from database.models.partnership_model import PartnershipDao
from database.models.channel_post_model import ChannelPostDao
from database.models.post_message_model import PostMessageDao
from database.models.channel_user_model import ChannelUserDao
from database.models.product_review_model import ProductReviewDao
from database.models.custom_bot_user_model import CustomBotUserDao
from database.models.post_message_media_files import PostMessageMediaFileDao
from database.models import Base  # should be the last import from database.models

from common_utils.singleton import singleton


@singleton
class Database:
    def __init__(self, sqlalchemy_url: str, logger) -> None:
        self.engine = create_async_engine(sqlalchemy_url)
        self.logger = logger

        self.bot_dao = BotDao(self.engine, self.logger)
        self.adv_dao = AdvDao(self.engine, self.logger)
        self.user_dao = UserDao(self.engine, self.logger)
        self.order_dao = OrderDao(self.engine, self.logger)
        self.product_dao = ProductDao(self.engine, self.logger)
        self.mailing_dao = MailingDao(self.engine, self.logger)
        self.contest_dao = ContestDao(self.engine, self.logger)
        self.payment_dao = PaymentDao(self.engine, self.logger)
        self.channel_dao = ChannelDao(self.engine, self.logger)
        self.category_dao = CategoryDao(self.engine, self.logger)
        self.user_role_dao = UserRoleDao(self.engine, self.logger)
        self.partnership_dao = PartnershipDao(self.engine, self.logger)
        self.post_message_dao = PostMessageDao(self.engine, self.logger)
        self.channel_user_dao = ChannelUserDao(self.engine, self.logger)
        self.channel_post_dao = ChannelPostDao(self.engine, self.logger)
        self.product_review_dao = ProductReviewDao(self.engine, self.logger)
        self.custom_bot_user_dao = CustomBotUserDao(self.engine, self.logger)
        self.post_message_media_file_dao = PostMessageMediaFileDao(self.engine, self.logger)

        self.logger.debug("Database class is initialized")

    async def connect(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.logger.debug("Metadata is used to create Tables")

    def get_bot_dao(self) -> BotDao:
        return self.bot_dao

    def get_adv_dao(self) -> AdvDao:
        return self.adv_dao

    def get_user_dao(self) -> UserDao:
        return self.user_dao

    def get_order_dao(self) -> OrderDao:
        return self.order_dao

    def get_product_db(self) -> ProductDao:
        return self.product_dao

    def get_payment_dao(self) -> PaymentDao:
        return self.payment_dao

    def get_channel_dao(self) -> ChannelDao:
        return self.channel_dao

    def get_mailing_dao(self) -> MailingDao:
        return self.mailing_dao

    def get_contest_dao(self) -> ContestDao:
        return self.contest_dao

    def get_category_dao(self) -> CategoryDao:
        return self.category_dao

    def get_user_role_dao(self) -> UserRoleDao:
        return self.user_role_dao

    def get_partnership_dao(self) -> PartnershipDao:
        return self.partnership_dao

    def get_post_message_dao(self) -> PostMessageDao:
        return self.post_message_dao

    def get_channel_user_dao(self) -> ChannelUserDao:
        return self.channel_user_dao

    def get_channel_post_dao(self) -> ChannelPostDao:
        return self.channel_post_dao

    def get_custom_bot_user_db(self) -> CustomBotUserDao:
        return self.custom_bot_user_dao

    def get_product_review_dao(self) -> ProductReviewDao:
        return self.product_review_dao

    def get_post_message_media_file_dao(self) -> PostMessageMediaFileDao:
        return self.post_message_media_file_dao
