from typing import Any

from aiogram.types import ChatMemberUpdated, ChatMemberLeft, ChatMemberAdministrator, ChatMemberBanned

from bot.keyboards import get_inline_bot_menu_keyboard
from bot.utils import MessageTexts
from custom_bots.handlers.routers import multi_bot_channel_router
from custom_bots.multibot import bot_db, logger, channel_db, main_bot
from database.models.channel_model import ChannelSchema


# @multi_bot_channel_router.my_chat_member()
# async def my_chat_member_handler(my_chat_member: ChatMemberUpdated) -> Any:
#     logger.info(f"Bot @{(await my_chat_member.bot.get_me()).username} has rights update in @{my_chat_member.chat.username}")
#
#     if my_chat_member.chat.type != "channel":
#         return
#
#     channel_username = my_chat_member.chat.username
#
#     custom_bot = await bot_db.get_bot_by_token(my_chat_member.bot.token)
#     custom_bot_username = (await my_chat_member.bot.get_me()).username
#
#     bot_id = custom_bot.bot_id
#     performed_by_admin = my_chat_member.from_user.id == custom_bot.created_by
#
#     channel_schema = ChannelSchema(
#             channel_id=my_chat_member.chat.id,
#             bot_id=bot_id,
#             added_by_admin=performed_by_admin
#     )
#
#     ## Bot added
#     if isinstance(my_chat_member.old_chat_member, (ChatMemberLeft, ChatMemberBanned)) and \
#             isinstance(my_chat_member.new_chat_member, ChatMemberAdministrator):
#         await channel_db.add_channel(channel_schema)
#         logger.info(
#             f"Bot @{custom_bot_username} added to @{channel_username}")
#
#         await main_bot.send_message(
#             chat_id=custom_bot.created_by,
#             text=MessageTexts.BOT_ADDED_TO_CHANNEL_MESSAGE.value.format(custom_bot_username, channel_username),
#             reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
#         )
#     ## Bot removed
#     elif isinstance(my_chat_member.new_chat_member, (ChatMemberLeft, ChatMemberBanned)):
#         await channel_db.delete_channel(channel_schema)
#         logger.info(
#             f"Bot @{(await my_chat_member.bot.get_me()).username} removed from @{my_chat_member.chat.username}")
#
#         await main_bot.send_message(
#             chat_id=custom_bot.created_by,
#             text=MessageTexts.BOT_REMOVED_FROM_CHANNEL_MESSAGE.value.format(custom_bot_username, channel_username),
#             reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
#         )