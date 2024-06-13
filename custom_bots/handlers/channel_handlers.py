from typing import Any, get_type_hints

from aiogram.types import ChatMemberUpdated, ChatMemberLeft, ChatMemberAdministrator, ChatMemberBanned

from bot.keyboards import get_inline_bot_menu_keyboard
from bot.utils import MessageTexts
from custom_bots.handlers.routers import multi_bot_channel_router
from custom_bots.multibot import bot_db, channel_db, main_bot, channel_user_db
from database.models.channel_model import ChannelSchema
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from logs.config import custom_bot_logger
from database.models.channel_user_model import ChannelUserSchema, ChannelUserNotFound, ChannelUserSchemaWithoutId

from datetime import datetime


@multi_bot_channel_router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    custom_bot_logger.info(
        f"User {user_id} joined chat {channel_id}")
    user_id = event.new_chat_member.user.id
    channel_id = event.chat.id
    try:
        channel_user = await channel_user_db.get_channel_user_by_channel_user_id_and_channel_id(user_id, channel_id)
        channel_user.join_date = datetime.now().replace(tzinfo=None)
        channel_user.is_channel_member = True
        await channel_user_db.update_channel_user(channel_user)
    except ChannelUserNotFound:
        custom_bot_logger.info(f"user {user_id} not found, adding to db")
        await channel_user_db.add_chanel_user(
            ChannelUserSchemaWithoutId.model_validate(
                {"channel_user_id": user_id, "channel_id": channel_id,
                    "join_date": datetime.now().replace(tzinfo=None),
                    "is_channel_member": True}
            )
        )


@ multi_bot_channel_router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_user_leave(event: ChatMemberUpdated):
    user_id = event.old_chat_member.user.id
    channel_id = event.chat.id
    custom_bot_logger.info(
        f"User {user_id} left chat {channel_id}")
    try:
        channel_user = await channel_user_db.get_channel_user_by_channel_user_id_and_channel_id(user_id, channel_id)
        channel_user.join_date = datetime.now().replace(tzinfo=None)
        channel_user.is_channel_member = False
        await channel_user_db.update_channel_user(channel_user)
    except ChannelUserNotFound:
        custom_bot_logger.info(f"user {user_id} not found, adding to db")
        await channel_user_db.add_chanel_user(
            ChannelUserSchemaWithoutId.model_validate(
                {"channel_user_id": user_id, "channel_id": channel_id,
                    "join_date": datetime.now().replace(tzinfo=None),
                    "is_channel_member": False}
            )
        )


@ multi_bot_channel_router.my_chat_member()
async def my_chat_member_handler(my_chat_member: ChatMemberUpdated) -> Any:
    custom_bot_logger.info(f"Bot @{(await my_chat_member.bot.get_me()).username} has rights update in @{my_chat_member.chat.username}")

    if my_chat_member.chat.type != "channel":
        return

    channel_username = my_chat_member.chat.username

    custom_bot = await bot_db.get_bot_by_token(my_chat_member.bot.token)
    custom_bot_username = (await my_chat_member.bot.get_me()).username

    bot_id = custom_bot.bot_id
    performed_by_admin = my_chat_member.from_user.id == custom_bot.created_by

    channel_schema = ChannelSchema(
        channel_id=my_chat_member.chat.id,
        bot_id=bot_id,
        added_by_admin=performed_by_admin
    )

    # Bot added
    if isinstance(my_chat_member.old_chat_member, (ChatMemberLeft, ChatMemberBanned)) and \
            isinstance(my_chat_member.new_chat_member, ChatMemberAdministrator):
        await channel_db.add_channel(channel_schema)
        custom_bot_logger.info(
            f"Bot @{custom_bot_username} added to @{channel_username}")

        await main_bot.send_message(
            chat_id=custom_bot.created_by,
            text=MessageTexts.BOT_ADDED_TO_CHANNEL_MESSAGE.value.format(
                custom_bot_username, channel_username),
            reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
        )
    # Bot removed
    elif isinstance(my_chat_member.new_chat_member, (ChatMemberLeft, ChatMemberBanned)):
        await channel_db.delete_channel(channel_schema)
        custom_bot_logger.info(
            f"Bot @{(await my_chat_member.bot.get_me()).username} removed from @{my_chat_member.chat.username}")

        await main_bot.send_message(
            chat_id=custom_bot.created_by,
            text=MessageTexts.BOT_REMOVED_FROM_CHANNEL_MESSAGE.value.format(
                custom_bot_username, channel_username),
            reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
        )
    elif isinstance(my_chat_member.new_chat_member, ChatMemberAdministrator):
        old_user = my_chat_member.old_chat_member
        new_user = my_chat_member.new_chat_member
        annotations = ChatMemberAdministrator.__annotations__
        # members = [attr for attr in dir(ChatMemberAdministrator) if not callable(
        #     getattr(ChatMemberAdministrator, attr)) and not attr.startswith("__")]
        final_message_text = f"Права бота в канале @{channel_username} изменены:\n\n"
        for member in annotations.keys():
            if member.startswith("can") is False:
                continue
            status = "✅" if getattr(new_user, member) else "❌"
            if getattr(old_user, member) == getattr(new_user, member):
                final_message_text += f"{member} {status}\n"
            else:
                final_message_text += f"{member} =====> {status}\n"

        await main_bot.send_message(
            chat_id=custom_bot.created_by,
            text=final_message_text,
            reply_markup=await get_inline_bot_menu_keyboard(custom_bot.bot_id)
        )
