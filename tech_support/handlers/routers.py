from common_utils.bot_filters import UserIdFilter
from common_utils.middlewaries.log_middleware import LogMiddleware
from common_utils.middlewaries.errors_middleware import ErrorMiddleware

from tech_support.bot import bot

from common_utils.config import tech_support_settings

from aiogram import Router

from logs.config import tech_support_logger


log_middleware = LogMiddleware(logger=tech_support_logger)
support_admins_filter = UserIdFilter(user_id=tech_support_settings.TECH_SUPPORT_ADMINS)
error_middleware = ErrorMiddleware(bot=bot)

users_router = Router(name="users")
users_router.message.outer_middleware(log_middleware)
users_router.callback_query.outer_middleware(log_middleware)
users_router.message.middleware(error_middleware)
users_router.callback_query.middleware(error_middleware)


admins_router = Router(name="admins")
admins_router.message.filter(support_admins_filter)
admins_router.callback_query.filter(support_admins_filter)
admins_router.message.outer_middleware(log_middleware)
admins_router.callback_query.outer_middleware(log_middleware)
admins_router.message.middleware(error_middleware)
admins_router.callback_query.middleware(error_middleware)
