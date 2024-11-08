from common_utils.config import database_settings

from database.models.models import Database
from database.models.bot_model import BotDao
from database.models.user_model import UserDao
from database.models.order_model import OrderDao
from database.models.option_model import OptionDao
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
from database.models.order_option_model import OrderOptionDao
from database.models.pickle_storage_model import PickleStorageDao
from database.models.product_review_model import ProductReviewDao
from database.models.custom_bot_user_model import CustomBotUserDao
from database.models.post_message_media_files import PostMessageMediaFileDao
from database.models.order_choose_option_model import OrderChooseOptionDao
from database.models.referral_invite_model import ReferralInviteDao

from logs.config import db_logger

db_engine: Database = Database(database_settings.SQLALCHEMY_URL, db_logger)

bot_db: BotDao = db_engine.get_bot_dao()
user_db: UserDao = db_engine.get_user_dao()
order_db: OrderDao = db_engine.get_order_dao()
pay_db: PaymentDao = db_engine.get_payment_dao()
option_db: OptionDao = db_engine.get_option_dao()
product_db: ProductDao = db_engine.get_product_db()
channel_db: ChannelDao = db_engine.get_channel_dao()
mailing_db: MailingDao = db_engine.get_mailing_dao()
contest_db: ContestDao = db_engine.get_contest_dao()
category_db: CategoryDao = db_engine.get_category_dao()
user_role_db: UserRoleDao = db_engine.get_user_role_dao()
order_option_db: OrderOptionDao = db_engine.get_order_option_dao()
pickle_store_db: PickleStorageDao = db_engine.get_pickle_store_dao()
partnership_db: PartnershipDao = db_engine.get_partnership_dao()
post_message_db: PostMessageDao = db_engine.get_post_message_dao()
channel_user_db: ChannelUserDao = db_engine.get_channel_user_dao()
channel_post_db: ChannelPostDao = db_engine.get_channel_post_dao()
product_review_db: ProductReviewDao = db_engine.get_product_review_dao()
custom_bot_user_db: CustomBotUserDao = db_engine.get_custom_bot_user_db()
referral_invite_db: ReferralInviteDao = db_engine.get_referral_invite_dao()
order_choose_option_db: OrderChooseOptionDao = db_engine.get_order_choose_option_dao()
post_message_media_file_db: PostMessageMediaFileDao = db_engine.get_post_message_media_file_dao()
