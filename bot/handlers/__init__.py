import bot.handlers.admin_bot_menu_handlers
import bot.handlers.command_handlers
import bot.handlers.custom_bot_editing_handlers
import bot.handlers.subscription_handlers
import bot.handlers.channel_settings_handlers
import bot.handlers.mailing_settings_handlers
import bot.handlers.stock_menu_handler
import bot.handlers.post_message_handlers

from .routers import (admin_bot_menu_router, channel_menu_router, commands_router, subscribe_router,
                      custom_bot_editing_router, stock_menu_router, post_message_router)
