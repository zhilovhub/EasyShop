from aiogram import Router

from bot.filters import ChatTypeFilter
from bot.middlewaries.subscription_middleware import CheckSubscriptionMiddleware
from bot.middlewaries.errors_middleware import ErrorMiddleware
from bot.middlewaries.log_middleware import MainLogMiddleware

custom_bot_editing_router = Router(name="custom_bot_editing")  # only for SUBSCRIBERS
custom_bot_editing_router.message.filter(ChatTypeFilter(chat_type="private"))
custom_bot_editing_router.message.outer_middleware(MainLogMiddleware())
custom_bot_editing_router.message.middleware(CheckSubscriptionMiddleware())
custom_bot_editing_router.callback_query.outer_middleware(MainLogMiddleware())
custom_bot_editing_router.callback_query.middleware(CheckSubscriptionMiddleware())
custom_bot_editing_router.message.middleware(ErrorMiddleware())
custom_bot_editing_router.callback_query.middleware(ErrorMiddleware())

admin_bot_menu_router = Router(name="admin_bot_menu")  # only for SUBSCRIBERS
admin_bot_menu_router.message.filter(ChatTypeFilter(chat_type="private"))
admin_bot_menu_router.message.outer_middleware(MainLogMiddleware())
admin_bot_menu_router.message.middleware(CheckSubscriptionMiddleware())
admin_bot_menu_router.callback_query.outer_middleware(MainLogMiddleware())
admin_bot_menu_router.callback_query.middleware(CheckSubscriptionMiddleware())
admin_bot_menu_router.message.middleware(ErrorMiddleware())
admin_bot_menu_router.callback_query.middleware(ErrorMiddleware())

channel_menu_router = Router(name="channel_menu")  # only for SUBSCRIBERS
channel_menu_router.message.filter(ChatTypeFilter(chat_type="private"))
channel_menu_router.message.outer_middleware(MainLogMiddleware())
channel_menu_router.message.middleware(CheckSubscriptionMiddleware())
channel_menu_router.callback_query.outer_middleware(MainLogMiddleware())
channel_menu_router.callback_query.middleware(CheckSubscriptionMiddleware())
channel_menu_router.message.middleware(ErrorMiddleware())
channel_menu_router.callback_query.middleware(ErrorMiddleware())

subscribe_router = Router(name="subscribe_router")
subscribe_router.message.filter(ChatTypeFilter(chat_type="private"))
subscribe_router.message.outer_middleware(MainLogMiddleware())
subscribe_router.message.middleware(ErrorMiddleware())
subscribe_router.callback_query.outer_middleware(MainLogMiddleware())
subscribe_router.callback_query.middleware(ErrorMiddleware())

commands_router = Router(name="commands")
commands_router.message.filter(ChatTypeFilter(chat_type="private"))
commands_router.message.outer_middleware(MainLogMiddleware())
commands_router.message.middleware(ErrorMiddleware())
commands_router.callback_query.outer_middleware(MainLogMiddleware())
commands_router.callback_query.middleware(ErrorMiddleware())

