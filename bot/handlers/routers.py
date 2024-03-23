from aiogram import Router

from bot.main import db_engine
from bot.filters import ChatTypeFilter
from bot.middlewaries.subscription_middleware import CheckSubscriptionMiddleware

from database.models.bot_model import BotDao
from database.models.user_model import UserDao
from database.models.order_model import OrderDao
from database.models.product_model import ProductDao
from database.models.payment_model import PaymentDao

for_subscribers_router = Router(name="for_subscribers_router")  # only for SUBSCRIBERS
for_subscribers_router.message.filter(ChatTypeFilter(chat_type='private'))
for_subscribers_router.message.middleware(CheckSubscriptionMiddleware())
for_subscribers_router.callback_query.middleware(CheckSubscriptionMiddleware())

custom_bot_editing_router = Router(name="custom_bot_editing")  # only for SUBSCRIBERS
custom_bot_editing_router.include_router(for_subscribers_router)
custom_bot_editing_router.message.filter(ChatTypeFilter(chat_type='private'))

admin_bot_menu_router = Router(name="admin_bot_menu")  # only for SUBSCRIBERS
admin_bot_menu_router.include_router(for_subscribers_router)
admin_bot_menu_router.message.filter(ChatTypeFilter(chat_type='private'))

subscribe_router = Router(name="subscribe_router")
subscribe_router.message.filter(ChatTypeFilter(chat_type='private'))

commands_router = Router(name="commands")
commands_router.message.filter(ChatTypeFilter(chat_type='private'))

bot_db: BotDao = db_engine.get_bot_dao()
user_db: UserDao = db_engine.get_user_dao()
order_db: OrderDao = db_engine.get_order_dao()
pay_db: PaymentDao = db_engine.get_payment_dao()
product_db: ProductDao = db_engine.get_product_db()  # TODO move it from here
