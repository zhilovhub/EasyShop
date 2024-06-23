from typing import Any, get_type_hints

from aiogram.types import ChatMemberUpdated, ChatMemberLeft, ChatMemberAdministrator, ChatMemberBanned, CallbackQuery, \
    Message

from bot.exceptions.exceptions import InstanceAlreadyExists
from bot.keyboards import get_contest_inline_join_button
from bot.keyboards.main_menu_keyboards import InlineBotMenuKeyboard
from bot.utils import MessageTexts
from custom_bots.handlers.routers import multi_bot_channel_router
from custom_bots.multibot import bot_db, channel_db, main_bot, channel_user_db, custom_ad_db, scheduler, \
    channel_post_db, contest_user_db
from database.models.channel_model import ChannelSchema
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter

from database.models.channel_post_model import ChannelPostNotFound
from logs.config import custom_bot_logger
from database.models.channel_user_model import ChannelUserSchema, ChannelUserNotFound, ChannelUserSchemaWithoutId
from custom_bots.multibot import order_db, product_db, bot_db, main_bot, PREV_ORDER_MSGS, custom_bot_user_db, CustomUserStates, QUESTION_MESSAGES, format_locales
from database.models.bot_model import BotNotFound
from database.models.custom_bot_user_model import CustomBotUserNotFound
from database.models.contest_user_model import ContestUserSchemaWithoutId

from datetime import datetime
from logs.config import extra_params


@multi_bot_channel_router.callback_query(lambda query: query.data.startswith("contest_join"))
async def register_contest_user(query: CallbackQuery):
    if query.message.chat.type != "channel":
        return
    user_id = query.from_user.id
    channel_id = query.message.chat.id
    try:
        bot = await bot_db.get_bot_by_token(query.message.bot.token)
        # custom_bot_logger.info(
        #     f"user_id={user_id}: user called /start at bot_id={bot.bot_id}",
        #     extra=extra_params(user_id=user_id, bot_id=bot.bot_id)
        # )

        try:
            await custom_bot_user_db.get_custom_bot_user(bot.bot_id, user_id)
        except CustomBotUserNotFound:
            # custom_bot_logger.info(
            #     f"user_id={user_id}: user not found in database, trying to add to it",
            #     extra=extra_params(user_id=user_id, bot_id=bot.bot_id)
            # )
            await custom_bot_user_db.add_custom_bot_user(bot.bot_id, user_id)
    except BotNotFound:
        return await query.answer("Бот не инициализирован", show_alert=True)

    try:
        channel_post = await channel_post_db.get_channel_post(channel_id, is_contest=True)
    except ChannelPostNotFound:
        return await query.answer(text="Конкурс уже закончен!")

    if channel_post.contest_end_date > datetime.now():
        try:
            await contest_user_db.add_contest_user(ContestUserSchemaWithoutId.model_validate(
                {"user_id": user_id, "channel_id": channel_id,
                    "join_date": datetime.now().replace(tzinfo=None), "contest_post_id": channel_post.channel_post_id}
            ))
            await query.answer(text="Вы успешно зарегистрировались!", show_alert=True)
            await query.message.edit_reply_markup(reply_markup=await get_contest_inline_join_button(channel_id))
        except InstanceAlreadyExists:
            await query.answer(text="Вы уже зарегистрировались!")
    else:
        await query.answer(text="Конкурс уже закончен!")


@multi_bot_channel_router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    user_id = event.new_chat_member.user.id
    channel_id = event.chat.id
    custom_bot_logger.info(
        f"User {user_id} joined chat {channel_id}")
    try:
        channel_user = await channel_user_db.get_channel_user_by_channel_user_id_and_channel_id(user_id, channel_id)
        channel_user.join_date = datetime.now().replace(tzinfo=None)
        channel_user.is_channel_member = True
        await channel_user_db.update_channel_user(channel_user)
    except ChannelUserNotFound:
        custom_bot_logger.info(f"user {user_id} not found, adding to db")
        await channel_user_db.add_channel_user(
            ChannelUserSchemaWithoutId.model_validate(
                {"channel_user_id": user_id, "channel_id": channel_id,
                 "join_date": datetime.now().replace(tzinfo=None),
                 "is_channel_member": True}
            )
        )


@multi_bot_channel_router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
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


@multi_bot_channel_router.my_chat_member()
async def my_chat_member_handler(my_chat_member: ChatMemberUpdated) -> Any:
    custom_bot_logger.info(
        f"Bot @{(await my_chat_member.bot.get_me()).username} has rights update in @{my_chat_member.chat.username}")

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
            reply_markup=await InlineBotMenuKeyboard.get_inline_bot_menu_keyboard(custom_bot.bot_id)
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
            reply_markup=await InlineBotMenuKeyboard.get_inline_bot_menu_keyboard(custom_bot.bot_id)
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
            reply_markup=await InlineBotMenuKeyboard.get_inline_bot_menu_keyboard(custom_bot.bot_id)
        )


@multi_bot_channel_router.channel_post()
async def channel_post_handler(message: Message):
    channel = await channel_db.get_channel(message.chat.id)
    bot_data = await bot_db.get_bot(channel.bot_id)
    if channel.is_ad_post_block:
        custom_bot_logger.debug(f"BOT_ID = {channel.bot_id} - "
                                f"channel post detected with after ad block enabled\nblock until: "
                                f"{channel.ad_post_block_until}\nnow: {datetime.now()}",
                                extra=extra_params(bot_id=channel.bot_id, channel_id=channel.channel_id))
        adv = await custom_ad_db.get_channel_last_custom_ad(channel_id=channel.channel_id)
        if channel.ad_post_block_until > datetime.now():
            channel.is_ad_post_block = False
            await channel_db.update_channel(channel)

            chat_data = await message.bot.get_chat(channel.channel_id)
            adv_user_data = await message.bot.get_chat(adv.by_user)

            await message.bot.send_message(bot_data.created_by,
                                           f"В канале <b>{('@' + chat_data.username) if chat_data.username else chat_data.full_name}</b> "
                                           f"было опубликовано сообщение, "
                                           f"рекламное предложение разорвано. "
                                           f"(от пользователя @{adv_user_data.username})")

            await message.bot.send_message(adv.by_user,
                                           f"В канале <b>{('@' + chat_data.username) if chat_data.username else chat_data.full_name}</b> "
                                           f"было опубликовано сообщение, "
                                           f"рекламное предложение разорвано.")
            adv.status = "canceled"
            await custom_ad_db.update_custom_ad(adv)
            job = await scheduler.get_job(adv.finish_job_id)
            await scheduler.del_job(job)
