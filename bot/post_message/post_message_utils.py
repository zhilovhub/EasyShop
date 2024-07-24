from aiogram.types import CallbackQuery

from bot.keyboards.post_message_keyboards import UnknownPostMessageType

from database.config import post_message_db, contest_db
from database.models.post_message_model import PostMessageSchema, PostMessageNotFoundError, PostMessageType
from database.models.post_message_media_files import PostMessageMediaFileSchema

from logs.config import extra_params, logger


async def is_post_message_valid(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        media_files: list[PostMessageMediaFileSchema]
) -> bool:
    match post_message_type:
        case PostMessageType.MAILING:
            pass
        case PostMessageType.CHANNEL_POST:
            pass
        case PostMessageType.CONTEST:
            contest = await contest_db.get_contest_by_post_message_id(post_message.post_message_id)
            if contest.finish_date is None:
                await query.answer(
                    "Введите дату окончания конкурса",
                    show_alert=True
                )
                return False
        case PostMessageType.PARTNERSHIP_POST:
            pass
        case _:
            raise UnknownPostMessageType

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
    except PostMessageNotFoundError as e:
        logger.info(
            f"user_id={user_id}: tried to edit post_message_id={post_message_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_idf=bot_id, post_message_id=post_message_id)
        )

        match post_message_type:
            case PostMessageType.MAILING:
                await query.answer("🚫 Рассылка уже завершена или удалена", show_alert=True)
            case PostMessageType.CHANNEL_POST:
                await query.answer("🚫 Запись в канал уже отправлена или удалена", show_alert=True)
            case PostMessageType.CONTEST:
                await query.answer("🚫 Конкурс в канал уже отправлен или удалён", show_alert=True)
            case PostMessageType.PARTNERSHIP_POST:
                await query.answer("🚫 Партнерский пост в канал уже отправлен или удалён", show_alert=True)
            case _:
                raise UnknownPostMessageType

        await query.message.delete()

        raise e
