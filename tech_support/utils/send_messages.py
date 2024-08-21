from aiogram.types import Message, ReplyKeyboardRemove

from common_utils.config import tech_support_settings

from tech_support.bot import bot, ADMIN_MESSAGES
from tech_support.keyboards.keyboards import AnswerKeyboard
from tech_support.utils.message_texts import MessageTexts as TechMessageTexts

from logs.config import tech_support_logger


async def send_message_to_admins(
    message: Message, lang: str, admins: list = tech_support_settings.TECH_SUPPORT_ADMINS, suggest: bool = False
):
    messages_data = ADMIN_MESSAGES.get_data()
    messages_data[f"{message.from_user.id}#{message.message_id}"] = []
    for admin in admins:
        try:
            if suggest:
                prefix = "[🆕 Предложение фичи]"
            else:
                prefix = "[❓ Вопрос]"
            text = prefix + (
                "\n\nОт пользователя:\n"
                f"\nUsername: @{message.from_user.username}"
                f"\nFull name: {message.from_user.full_name}"
                f"\nUID: {message.from_user.id}"
            )
            msg = await bot.send_message(chat_id=admin, text=text)
            await message.copy_to(
                reply_to_message_id=msg.message_id,
                chat_id=admin,
                reply_markup=AnswerKeyboard.get_keyboard(message.from_user.id, message.message_id),
            )
            messages_data[f"{message.from_user.id}#{message.message_id}"].append((admin, msg.message_id))
        except Exception as e:
            tech_support_logger.warning("cant copy message to tech support admin", exc_info=e)
    await message.reply(
        **TechMessageTexts.get_sended_message_text(lang).as_kwargs(), reply_markup=ReplyKeyboardRemove()
    )
    ADMIN_MESSAGES.update_data(messages_data)
