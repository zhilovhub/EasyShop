from aiogram.types import CallbackQuery

from bot.main import post_message_db
from bot.enums.post_message_type import PostMessageType
from bot.keyboards.post_message_keyboards import UnknownPostMessageType

from database.models.post_message_model import PostMessageSchema, PostMessageNotFound
from database.models.post_message_media_files import PostMessageMediaFileSchema

from logs.config import extra_params, logger


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


async def get_post_message(
        query: CallbackQuery,
        user_id: int,
        bot_id: int,
        post_message_id: int,
        post_message_type: PostMessageType
) -> PostMessageSchema:
    try:
        post_message = await post_message_db.get_post_message(post_message_id)
        return post_message
    except PostMessageNotFound as e:
        logger.info(
            f"user_id={user_id}: tried to edit post_message_id={post_message_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_idf=bot_id, post_message_id=post_message_id)
        )

        match post_message_type:
            case PostMessageType.MAILING:
                await query.answer("Рассылка уже завершена или удалена", show_alert=True)
            case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
                await query.answer("Запись в канал уже отправлена или удалена", show_alert=True)
            case _:
                raise UnknownPostMessageType

        await query.message.delete()

        raise e
