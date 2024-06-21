from aiogram import Bot


async def send_start_message_to_admins(bot: Bot, admins: list[int], msg_text: str, disable_notification: bool = False):
    for admin_id in admins:
        try:
            await bot.send_message(chat_id=admin_id, text=msg_text, disable_notification=disable_notification)
        except:
            pass
