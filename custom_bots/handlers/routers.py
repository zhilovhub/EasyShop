from aiogram import Router

from common_utils.middlewaries.lang_middleware import LangCheckMiddleware
from common_utils.middlewaries.log_middleware import LogMiddleware
from common_utils.middlewaries.errors_middleware import ErrorMiddleware

from logs.config import custom_bot_logger

log_middleware = LogMiddleware(logger=custom_bot_logger)
lang_middleware = LangCheckMiddleware(from_main_bot=False)

multi_bot_raw_router = Router(name="raw")
multi_bot_raw_router.message.outer_middleware(log_middleware)
multi_bot_raw_router.callback_query.outer_middleware(log_middleware)
multi_bot_raw_router.message.middleware(ErrorMiddleware())
multi_bot_raw_router.callback_query.middleware(ErrorMiddleware())

multi_bot_router = Router(name="multibot")
multi_bot_router.message.outer_middleware(log_middleware)
multi_bot_router.callback_query.outer_middleware(log_middleware)
multi_bot_router.message.middleware(ErrorMiddleware())
multi_bot_router.callback_query.middleware(ErrorMiddleware())
multi_bot_router.message.middleware(lang_middleware)
multi_bot_router.callback_query.middleware(lang_middleware)

multi_bot_channel_router = Router(name="channels")
multi_bot_channel_router.message.outer_middleware(log_middleware)
multi_bot_channel_router.callback_query.outer_middleware(log_middleware)
multi_bot_channel_router.my_chat_member.outer_middleware(log_middleware)
multi_bot_channel_router.my_chat_member.middleware(ErrorMiddleware())
multi_bot_channel_router.chat_member.middleware(ErrorMiddleware())
multi_bot_channel_router.callback_query.middleware(ErrorMiddleware())
multi_bot_channel_router.chat_member.outer_middleware(log_middleware)
multi_bot_channel_router.message.middleware(lang_middleware)
multi_bot_channel_router.callback_query.middleware(lang_middleware)

payment_router = Router(name="payment")
payment_router.message.outer_middleware(log_middleware)
payment_router.message.middleware(ErrorMiddleware())
payment_router.callback_query.outer_middleware(log_middleware)
payment_router.callback_query.middleware(ErrorMiddleware())
payment_router.pre_checkout_query.outer_middleware(log_middleware)
payment_router.pre_checkout_query.middleware(ErrorMiddleware())
payment_router.message.middleware(lang_middleware)
payment_router.callback_query.middleware(lang_middleware)

inline_mode_router = Router(name="inline")
inline_mode_router.inline_query.outer_middleware(log_middleware)
inline_mode_router.inline_query.middleware(ErrorMiddleware())
inline_mode_router.inline_query.middleware(lang_middleware)
