from common_utils.env_config import SQLALCHEMY_URL

from database.models.models import Database
from database.models.adv_model import AdvDao
from database.models.bot_model import BotDao
from database.models.user_model import UserDao
from database.models.order_model import OrderDao
from database.models.channel_model import ChannelDao
from database.models.contest_model import ContestDao
from database.models.mailing_model import MailingDao
from database.models.payment_model import PaymentDao
from database.models.product_model import ProductDao
from database.models.category_model import CategoryDao
from database.models.user_role_model import UserRoleDao
from database.models.partnership_model import PartnershipDao
from database.models.channel_post_model import ChannelPostDao
from database.models.channel_user_model import ChannelUserDao
from database.models.post_message_model import PostMessageDao
from database.models.product_review_model import ProductReviewDao
from database.models.custom_bot_user_model import CustomBotUserDao
from database.models.post_message_media_files import PostMessageMediaFileDao

from logs.config import db_logger

db_engine: Database = Database(SQLALCHEMY_URL, db_logger)

bot_db: BotDao = db_engine.get_bot_dao()
adv_db: AdvDao = db_engine.get_adv_dao()
user_db: UserDao = db_engine.get_user_dao()
order_db: OrderDao = db_engine.get_order_dao()
pay_db: PaymentDao = db_engine.get_payment_dao()
product_db: ProductDao = db_engine.get_product_db()
channel_db: ChannelDao = db_engine.get_channel_dao()
mailing_db: MailingDao = db_engine.get_mailing_dao()
contest_db: ContestDao = db_engine.get_contest_dao()
category_db: CategoryDao = db_engine.get_category_dao()
user_role_db: UserRoleDao = db_engine.get_user_role_dao()
partnership_db: PartnershipDao = db_engine.get_partnership_dao()
post_message_db: PostMessageDao = db_engine.get_post_message_dao()
channel_user_db: ChannelUserDao = db_engine.get_channel_user_dao()
channel_post_db: ChannelPostDao = db_engine.get_channel_post_dao()
product_review_db: ProductReviewDao = db_engine.get_product_review_dao()
custom_bot_user_db: CustomBotUserDao = db_engine.get_custom_bot_user_db()
post_message_media_file_db: PostMessageMediaFileDao = db_engine.get_post_message_media_file_dao()
