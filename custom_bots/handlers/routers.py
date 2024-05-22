from aiogram import Router

from bot.middlewaries.errors_middleware import ErrorMiddleware

multi_bot_router = Router(name="multibot")
multi_bot_router.message.middleware(ErrorMiddleware())
multi_bot_router.callback_query.middleware(ErrorMiddleware())

multi_bot_channel_router = Router(name="channels")
multi_bot_channel_router.my_chat_member.middleware(ErrorMiddleware())
