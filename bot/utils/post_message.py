import re
from enum import Enum

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.mailing_settings_handlers import PostActionType, send_post_message
from bot.keyboards import get_inline_bot_channel_post_menu_keyboard
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard, ReplyBackPostMessageMenuKeyboard
from bot.main import bot_db, post_message_db, bot, post_message_media_file_db, channel_post_db
from bot.states import States
from bot.utils import MessageTexts


class UnknownPostMessageType(Exception):
    pass


class PostMessageType(Enum):
    """For what is post message?"""
    MAILING = (
        "post_message_id",
        MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value,
        InlinePostMessageMenuKeyboard
    )
    CHANNEL_POST = (
        "channel_id",
        MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value,
        get_inline_bot_channel_post_menu_keyboard
    )


async def edit_button_url(message: Message, state: FSMContext, post_message_type: PostMessageType):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data[post_message_type.value[0]]

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    match post_message_type:
        case PostMessageType.MAILING:
            post_message = await post_message_db.get_post_message(post_message_id)
        case PostMessageType.CHANNEL_POST:
            post_message = await channel_post_db.get_channel_post(channel_id=post_message_id, is_contest=False)
        case _:
            raise UnknownPostMessageType

    if not post_message.has_button:
        return await _reply_no_button(message, bot_id, custom_bot_username, state)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username)
        else:
            pattern = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+" \
                      r"|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
            if not re.fullmatch(pattern, message.text):
                return await message.answer(
                    "Невалидная ссылка. Введите, пожалуйста, ссылку в стандартном формате, "
                    "начинающемся с <b>http</b> или <b>https</b>"
                )

            post_message.button_url = message.text  # TODO can be channel
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)  # TODO can be channel
            await post_message_db.update_post_message(post_message)  # TODO can be channel

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            # TODO can be this
            # await send_channel_post_message(
            #     bot,
            #     message.from_user.id,
            #     channel_post,
            #     media_files,
            #     MailingMessageType.AFTER_REDACTING,
            #     message.from_user.id,
            #     message.message_id,
            # )
            await send_post_message(
                bot,
                message.from_user.id,
                post_message,
                media_files,
                PostActionType.AFTER_REDACTING,
                message
            )
            await message.answer(
                MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)  # TODO ofcourse can be a channel
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer("Ссылка должна содержать только текст")


async def _reply_no_button(
        message: Message,
        bot_id: int,
        object_username: str,
        state: FSMContext,
        post_message_type: PostMessageType
) -> None:
    state_data = await state.get_data()

    await message.answer(
        "В настраиваемом сообщении кнопки уже нет",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
    )
    await message.answer(
        post_message_type.value[1].format(object_username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)  # TODO make common keyboard
    )

    await state.set_state(States.BOT_MENU)
    await state.set_data(state_data)


async def _back_to_post_message_menu(message: Message, bot_id: int, custom_bot_username: str) -> None:
    await message.answer(
        "Возвращаемся в меню...",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
    )
    await message.answer(
        text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),  # TODO here can be channel message
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)  # TODO there are some diffs between mailing and channel
    )
