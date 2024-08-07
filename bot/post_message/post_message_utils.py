from aiogram.types import CallbackQuery, Message

from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard
from database.config import post_message_db, contest_db
from database.models.post_message_model import PostMessageSchema, PostMessageNotFoundError, PostMessageType, \
    UnknownPostMessageTypeError
from database.models.post_message_media_files import PostMessageMediaFileSchema

from logs.config import extra_params, logger


async def is_post_message_valid(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        media_files: list[PostMessageMediaFileSchema]
) -> bool:
    """
    Check if Post Message is valid for telegram and specific post_message_type

    :raises UnknownPostMessageTypeError:
    """
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
            raise UnknownPostMessageTypeError

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
        event: Message | CallbackQuery,
        user_id: int,
        bot_id: int,
        post_message_id: int,
        post_message_type: PostMessageType | int
) -> PostMessageSchema:
    """
    Returns post message or answers that it doesn't exists anymore

    :raises PostMessageNotFoundError:
    :raises UnknownPostMessageTypeError:
    """

    try:
        post_message = await post_message_db.get_post_message(post_message_id)
        return post_message
    except PostMessageNotFoundError as e:
        if isinstance(event, Message):
            is_message = True
        else:
            is_message = False

        logger.info(
            f"user_id={user_id}: tried to edit post_message_id={post_message_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_idf=bot_id, post_message_id=post_message_id)
        )

        match post_message_type:
            case PostMessageType.MAILING | PostMessageType.MAILING.value:
                text = "🚫 Рассылка уже завершена или удалена"
            case PostMessageType.CHANNEL_POST | PostMessageType.CHANNEL_POST.value:
                text = "🚫 Запись в канал уже отправлена или удалена"
            case PostMessageType.CONTEST | PostMessageType.CONTEST.value:
                text = "🚫 Конкурс в канал уже отправлен или удалён"
            case PostMessageType.PARTNERSHIP_POST | PostMessageType.PARTNERSHIP_POST.value:
                text = "🚫 Партнерский пост в канал уже отправлен или удалён"
            case _:
                raise UnknownPostMessageTypeError

        if is_message:
            await event.answer(text, reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id))
        else:
            await event.answer(text, show_alert=True)
            await event.message.delete()

        raise e


def get_channel_id_from_query(callback_data, post_message_type: PostMessageType) -> int | None:
    """Пытается достать channel_id из определенных типов PostMessage, которые хранят в себе информацию о канале"""

    if post_message_type in (PostMessageType.CHANNEL_POST, PostMessageType.CONTEST):
        return callback_data.channel_id
    else:
        return None


def get_channel_id_from_state_data(state_data, post_message_type: PostMessageType) -> int | None:
    """Пытается достать channel_id из определенных типов PostMessage, которые хранят в себе информацию о канале"""

    if post_message_type in (PostMessageType.CHANNEL_POST, PostMessageType.CONTEST):
        return state_data["channel_id"]
    else:
        return None
