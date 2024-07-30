from aiogram import Router

from common_utils.middlewaries.log_middleware import LogMiddleware
from common_utils.middlewaries.errors_middleware import ErrorMiddleware

from logs.config import custom_bot_logger

log_middleware = LogMiddleware(logger=custom_bot_logger)

multi_bot_router = Router(name="multibot")
multi_bot_router.message.outer_middleware(log_middleware)
multi_bot_router.callback_query.outer_middleware(log_middleware)
multi_bot_router.message.middleware(ErrorMiddleware())
multi_bot_router.callback_query.middleware(ErrorMiddleware())

multi_bot_channel_router = Router(name="channels")
multi_bot_channel_router.message.outer_middleware(log_middleware)
multi_bot_channel_router.callback_query.outer_middleware(log_middleware)
multi_bot_channel_router.my_chat_member.outer_middleware(log_middleware)
multi_bot_channel_router.my_chat_member.middleware(ErrorMiddleware())
multi_bot_channel_router.chat_member.middleware(ErrorMiddleware())
multi_bot_channel_router.callback_query.middleware(ErrorMiddleware())
multi_bot_channel_router.chat_member.outer_middleware(log_middleware)

inline_mode_router = Router(name="inline")
inline_mode_router.inline_query.outer_middleware(log_middleware)
