import custom_bots.handlers.command_handlers
import custom_bots.handlers.handlers
import custom_bots.handlers.channel_handlers
import custom_bots.handlers.order_handlers
import custom_bots.handlers.question_handlers
import custom_bots.handlers.payments_handler
import custom_bots.handlers.inline_mode_handler

from .routers import (
    multi_bot_router,
    multi_bot_channel_router,
    inline_mode_router,
    payment_router,
    multi_bot_raw_router,
)
