from aiogram import Router

from bot.filters import ChatTypeFilter
from bot.middlewaries.subscription_middleware import CheckSubscriptionMiddleware

custom_bot_editing_router = Router(name="custom_bot_editing")  # only for SUBSCRIBERS
custom_bot_editing_router.message.filter(ChatTypeFilter(chat_type='private'))

admin_bot_menu_router = Router(name="admin_bot_menu")  # only for SUBSCRIBERS
admin_bot_menu_router.message.filter(ChatTypeFilter(chat_type='private'))

for_subscribers_router = Router(name="for_subscribers_router")  # only for SUBSCRIBERS
for_subscribers_router.message.filter(ChatTypeFilter(chat_type='private'))
for_subscribers_router.message.middleware(CheckSubscriptionMiddleware())
for_subscribers_router.callback_query.middleware(CheckSubscriptionMiddleware())
for_subscribers_router.include_router(admin_bot_menu_router)
for_subscribers_router.include_router(custom_bot_editing_router)

subscribe_router = Router(name="subscribe_router")
subscribe_router.message.filter(ChatTypeFilter(chat_type='private'))

commands_router = Router(name="commands")
commands_router.message.filter(ChatTypeFilter(chat_type='private'))
