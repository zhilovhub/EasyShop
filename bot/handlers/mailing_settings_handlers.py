import asyncio

from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties, Bot

from bot.main import bot, custom_bot_user_db, post_message_db
from bot.post_message.post_message_editors import PostActionType, send_post_message

from logs.config import logger


async def send_post_messages(custom_bot, post_message, media_files, chat_id):
    post_message_id = post_message.post_message_id
    all_custom_bot_users = await custom_bot_user_db.get_custom_bot_users(custom_bot.bot_id)
    custom_bot_tg = Bot(custom_bot.token, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML))

    for ind, user in enumerate(all_custom_bot_users, start=1):
        post_message = await post_message_db.get_post_message(post_message_id)

        if not post_message.is_running:
            post_message.sent_post_message_amount = 0
            await post_message_db.update_post_message(post_message)
            return

        await send_post_message(
            bot_from_send=custom_bot_tg,
            to_chat_id=user.user_id,
            post_message_schema=post_message,
            media_files=media_files,
            post_action_type=PostActionType.RELEASE,
            message=None,
        )

        logger.info(
            f"post_message with post_message_id {post_message_id} has "
            f"sent to {ind}/{len(all_custom_bot_users)} with user_id {user.user_id}"
        )
        # 20 messages per second (limit is 30)
        await asyncio.sleep(.05)
        post_message.sent_post_message_amount += 1
        await post_message_db.update_post_message(post_message)

    await bot.send_message(
        chat_id,
        f"Рассылка завершена\nСообщений отправлено - "
        f"{post_message.sent_post_message_amount}/{len(all_custom_bot_users)}"
    )

    post_message.is_running = False
    post_message.sent_post_message_amount = 0

    await asyncio.sleep(10)
    await post_message_db.delete_post_message(post_message.post_message_id)
