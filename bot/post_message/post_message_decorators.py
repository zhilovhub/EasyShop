from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.enums.post_message_type import PostMessageType
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard, UnknownPostMessageType, \
    InlinePostMessageExtraSettingsKeyboard, InlinePostMessageStartConfirmKeyboard, \
    InlinePostMessageAcceptDeletingKeyboard
from bot.main import bot_db
from bot.post_message.post_message_utils import get_post_message
from bot.utils import MessageTexts
from database.models.post_message_model import PostMessageNotFound
from logs.config import logger, extra_params


class UnknownFuncInDecorator(Exception):
    def __init__(self, func, decorator):
        self.func = func
        self.decorator = decorator

    def __str__(self) -> str:
        return f"{self.func.__name__} is not expected in decorator {self.decorator.__name__}"


def check_callback_conflicts(func):
    async def wrapper_func(query: CallbackQuery, state: FSMContext):
        match func.__name__:
            case "post_message_menu_callback_handler":
                callback_data = InlinePostMessageMenuKeyboard.Callback.model_validate_json(query.data)
            case "post_message_extra_settings_callback_handler":
                callback_data = InlinePostMessageExtraSettingsKeyboard.Callback.model_validate_json(query.data)
            case "post_message_confirm_start_callback_handler":
                callback_data = InlinePostMessageStartConfirmKeyboard.Callback.model_validate_json(query.data)
            case "post_message_accept_deleting_callback_handler":
                callback_data = InlinePostMessageAcceptDeletingKeyboard.Callback.model_validate_json(query.data)
            case _:
                raise UnknownFuncInDecorator(func, check_callback_conflicts)

        user_id = query.from_user.id
        bot_id = callback_data.bot_id
        post_message_type = callback_data.post_message_type

        try:
            post_message = await get_post_message(
                query, user_id, bot_id, callback_data.post_message_id, post_message_type
            )
        except PostMessageNotFound:
            return

        custom_bot_token = (await bot_db.get_bot(bot_id)).token
        print(callback_data)
        match post_message_type:
            case PostMessageType.MAILING:
                username = (await Bot(custom_bot_token).get_me()).username
            case PostMessageType.CHANNEL_POST:
                username = (await Bot(custom_bot_token).get_chat(callback_data.channel_id)).username
            case PostMessageType.CONTEST:
                username = (await Bot(custom_bot_token).get_chat(callback_data.channel_id)).username
            case _:
                raise UnknownPostMessageType

        match post_message_type:
            case PostMessageType.MAILING:  # specific buttons for mailing
                if callback_data.a not in (
                        InlinePostMessageMenuKeyboard.Callback.ActionEnum.STATISTICS,
                        InlinePostMessageMenuKeyboard.Callback.ActionEnum.CANCEL,
                        InlinePostMessageAcceptDeletingKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU,
                        InlinePostMessageExtraSettingsKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU,
                        InlinePostMessageStartConfirmKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU,
                ) and post_message.is_running:
                    await query.answer(
                        MessageTexts.bot_post_already_started_message(post_message_type),
                        show_alert=True
                    )
                    await query.message.edit_text(
                        text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(username),
                        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                            bot_id,
                            post_message_type,
                            channel_id=callback_data.channel_id
                            if post_message_type in (PostMessageType.CHANNEL_POST, PostMessageType.CONTEST) else None
                        ),
                        parse_mode=ParseMode.HTML
                    )
                    return

            case PostMessageType.CHANNEL_POST:  # specific buttons for channel post
                pass

        try:
            return await func(query, state, callback_data, post_message)
        except TypeError:
            return await func(query, callback_data, post_message)
        except Exception as e:
            logger.error(
                "Unexpected args",
                exc_info=e,
                extra=extra_params(
                    user_id=user_id, bot_id=bot_id, post_message_id=post_message.post_message_id
                )
            )
            raise e

    return wrapper_func
