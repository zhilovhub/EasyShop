from aiogram import Router

from bot.filters import ChatTypeFilter

router = Router(name="users")
router.message.filter(ChatTypeFilter(chat_type='private'))

commands_router = Router(name="commands")
commands_router.message.filter(ChatTypeFilter(chat_type='private'))

custom_bot_editing_router = Router(name="custom_bot_editing")
custom_bot_editing_router.message.filter(ChatTypeFilter(chat_type='private'))

admin_bot_menu_router = Router(name="admin_bot_menu")
admin_bot_menu_router.message.filter(ChatTypeFilter(chat_type='private'))
