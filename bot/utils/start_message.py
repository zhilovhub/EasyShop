from aiogram import Bot

from logs.config import logger, extra_params


async def send_start_message_to_admins(bot: Bot, admins: list[int], msg_text: str, disable_notification: bool = False):
    for admin_id in admins:
        try:
            await bot.send_message(chat_id=admin_id, text=msg_text, disable_notification=disable_notification)
        except Exception as e:
            logger.warning(
                "Unable send start message to admin",
                exc_info=e,
                extra=extra_params(user_id=admin_id)
            )
