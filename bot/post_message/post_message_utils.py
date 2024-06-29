from aiogram.types import CallbackQuery

from database.models.post_message_model import PostMessageSchema
from database.models.post_message_media_files import PostMessageMediaFileSchema


async def is_post_message_valid(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        media_files: list[PostMessageMediaFileSchema]
) -> bool:
    if len(media_files) > 1 and post_message.has_button:
        await query.answer(
            "Telegram не позволяет прикрепить кнопку, если в сообщении минимум 2 медиафайла",
            show_alert=True
        )
        return False
    elif not media_files and not post_message.description:
        await query.answer(
            text="В Вашем рассылочном сообщении нет ни текста, ни медиафайлов",
            show_alert=True
        )
        return False

    return True
