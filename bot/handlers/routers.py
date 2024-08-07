from aiogram import Router

from bot.filters import ChatTypeFilter, ChatId, IsTechAdmin
from bot.middlewaries.check_role_middleware import CheckRoleMiddleware
from bot.middlewaries.maintenance_middleware import MaintenanceMiddleware
from bot.middlewaries.subscription_middleware import CheckSubscriptionMiddleware

from common_utils.config import common_settings
from common_utils.middlewaries.log_middleware import LogMiddleware
from common_utils.middlewaries.errors_middleware import ErrorMiddleware

from logs.config import logger

log_middleware = LogMiddleware(logger=logger)

custom_bot_editing_router = Router(name="custom_bot_editing")  # only for SUBSCRIBERS
custom_bot_editing_router.message.filter(ChatTypeFilter(chat_type="private"))
custom_bot_editing_router.message.outer_middleware(log_middleware)
custom_bot_editing_router.message.outer_middleware(MaintenanceMiddleware())
custom_bot_editing_router.message.middleware(CheckSubscriptionMiddleware())
custom_bot_editing_router.callback_query.outer_middleware(log_middleware)
custom_bot_editing_router.callback_query.outer_middleware(MaintenanceMiddleware())
custom_bot_editing_router.callback_query.middleware(CheckSubscriptionMiddleware())
custom_bot_editing_router.message.middleware(ErrorMiddleware())
custom_bot_editing_router.callback_query.middleware(ErrorMiddleware())
custom_bot_editing_router.callback_query.middleware(CheckRoleMiddleware())
custom_bot_editing_router.message.middleware(CheckRoleMiddleware())

admin_bot_menu_router = Router(name="admin_bot_menu")  # only for SUBSCRIBERS
admin_bot_menu_router.message.filter(ChatTypeFilter(chat_type="private"))
admin_bot_menu_router.message.outer_middleware(log_middleware)
admin_bot_menu_router.message.outer_middleware(MaintenanceMiddleware())
admin_bot_menu_router.message.middleware(CheckSubscriptionMiddleware())
admin_bot_menu_router.callback_query.outer_middleware(log_middleware)
admin_bot_menu_router.callback_query.outer_middleware(MaintenanceMiddleware())
admin_bot_menu_router.callback_query.middleware(CheckSubscriptionMiddleware())
admin_bot_menu_router.message.middleware(ErrorMiddleware())
admin_bot_menu_router.callback_query.middleware(ErrorMiddleware())
admin_bot_menu_router.callback_query.middleware(CheckRoleMiddleware())
admin_bot_menu_router.message.middleware(CheckRoleMiddleware())

post_message_router = Router(name="post_message")  # only for SUBSCRIBERS
post_message_router.message.filter(ChatTypeFilter(chat_type="private"))
post_message_router.message.outer_middleware(log_middleware)
post_message_router.message.outer_middleware(MaintenanceMiddleware())
post_message_router.message.middleware(CheckSubscriptionMiddleware())
post_message_router.callback_query.outer_middleware(log_middleware)
post_message_router.callback_query.outer_middleware(MaintenanceMiddleware())
post_message_router.callback_query.middleware(CheckSubscriptionMiddleware())
post_message_router.message.middleware(ErrorMiddleware())
post_message_router.callback_query.middleware(ErrorMiddleware())
post_message_router.callback_query.middleware(CheckRoleMiddleware())
post_message_router.message.middleware(CheckRoleMiddleware())

channel_menu_router = Router(name="channel_menu")  # only for SUBSCRIBERS
channel_menu_router.message.filter(ChatTypeFilter(chat_type="private"))
channel_menu_router.message.outer_middleware(log_middleware)
channel_menu_router.message.outer_middleware(MaintenanceMiddleware())
channel_menu_router.message.middleware(CheckSubscriptionMiddleware())
channel_menu_router.callback_query.outer_middleware(log_middleware)
channel_menu_router.callback_query.outer_middleware(MaintenanceMiddleware())
channel_menu_router.callback_query.middleware(CheckSubscriptionMiddleware())
channel_menu_router.message.middleware(ErrorMiddleware())
channel_menu_router.callback_query.middleware(ErrorMiddleware())
channel_menu_router.callback_query.middleware(CheckRoleMiddleware())
channel_menu_router.message.middleware(CheckRoleMiddleware())

stock_menu_router = Router(name="stock_menu")  # only for SUBSCRIBERS
stock_menu_router.message.filter(ChatTypeFilter(chat_type="private"))
stock_menu_router.message.middleware(CheckSubscriptionMiddleware())
stock_menu_router.callback_query.middleware(CheckSubscriptionMiddleware())
stock_menu_router.message.middleware(ErrorMiddleware())
stock_menu_router.callback_query.middleware(ErrorMiddleware())
stock_menu_router.message.outer_middleware(log_middleware)
stock_menu_router.callback_query.outer_middleware(log_middleware)
stock_menu_router.message.outer_middleware(MaintenanceMiddleware())
stock_menu_router.callback_query.outer_middleware(MaintenanceMiddleware())
stock_menu_router.callback_query.middleware(CheckRoleMiddleware())
stock_menu_router.message.middleware(CheckRoleMiddleware())

subscribe_router = Router(name="subscribe_router")
subscribe_router.message.filter(ChatTypeFilter(chat_type="private"))
subscribe_router.message.outer_middleware(log_middleware)
subscribe_router.message.middleware(ErrorMiddleware())
subscribe_router.callback_query.outer_middleware(log_middleware)
subscribe_router.callback_query.middleware(ErrorMiddleware())
subscribe_router.message.outer_middleware(MaintenanceMiddleware())
subscribe_router.callback_query.outer_middleware(MaintenanceMiddleware())

admin_group_commands_router = Router(name="admin_group_commands_router")  # only for ADMINS' GROUP
admin_group_commands_router.message.filter(ChatTypeFilter(chat_type=["group", "supergroup"]))
admin_group_commands_router.message.filter(ChatId(chat_id=int(common_settings.ADMIN_GROUP_ID)))
admin_group_commands_router.message.filter(IsTechAdmin())
admin_group_commands_router.callback_query.filter(IsTechAdmin())
admin_group_commands_router.message.outer_middleware(log_middleware)
admin_group_commands_router.callback_query.outer_middleware(log_middleware)
admin_group_commands_router.message.middleware(ErrorMiddleware())
admin_group_commands_router.callback_query.middleware(ErrorMiddleware())

commands_router = Router(name="commands")
commands_router.message.filter(ChatTypeFilter(chat_type="private"))
commands_router.message.outer_middleware(log_middleware)
commands_router.message.middleware(ErrorMiddleware())
commands_router.callback_query.outer_middleware(log_middleware)
commands_router.callback_query.middleware(ErrorMiddleware())
commands_router.message.outer_middleware(MaintenanceMiddleware())
commands_router.callback_query.outer_middleware(MaintenanceMiddleware())
