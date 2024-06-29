from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.main import post_message_db, bot_db, post_message_media_file_db, _scheduler
from bot.utils import MessageTexts
from bot.states import States
from bot.handlers.routers import post_message_router
from bot.enums.post_message_type import PostMessageType
from bot.keyboards.channel_keyboards import InlineChannelMenuKeyboard
from bot.keyboards.main_menu_keyboards import InlineBotMenuKeyboard, ReplyBotMenuKeyboard
from bot.post_message.post_message_utils import is_post_message_valid, get_post_message
from bot.keyboards.post_message_keyboards import InlinePostMessageStartConfirmKeyboard, InlinePostMessageMenuKeyboard, \
    InlinePostMessageExtraSettingsKeyboard, InlinePostMessageAcceptDeletingKeyboard, UnknownPostMessageType
from bot.post_message.post_message_editors import edit_delay_date, edit_message, edit_button_text, edit_button_url, \
    edit_media_files, send_post_message, PostActionType
from bot.handlers.mailing_settings_handlers import send_post_messages
from bot.post_message.post_message_callback_handler import post_message_handler

from database.models.post_message_model import PostMessageNotFound, PostMessageSchema


@post_message_router.callback_query(lambda query: InlinePostMessageMenuKeyboard.callback_validator(query.data))
async def post_message_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    await post_message_handler(query, state)


@post_message_router.message(StateFilter(
    States.EDITING_POST_TEXT,
    States.EDITING_POST_BUTTON_TEXT,
    States.EDITING_POST_BUTTON_URL,
    States.EDITING_POST_MEDIA_FILES,
    States.EDITING_POST_DELAY_DATE,
))
async def editing_post_message_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    current_state = await state.get_state()

    match state_data["post_message_type"]:
        case PostMessageType.MAILING.value:
            post_message_type = PostMessageType.MAILING
        case PostMessageType.CHANNEL_POST.value:
            post_message_type = PostMessageType.CHANNEL_POST
        case _:
            raise UnknownPostMessageType

    match current_state:
        case States.EDITING_POST_DELAY_DATE:
            await edit_delay_date(message, state, post_message_type)
        case States.EDITING_POST_TEXT:
            await edit_message(message, state, post_message_type)
        case States.EDITING_POST_BUTTON_TEXT:
            await edit_button_text(message, state, post_message_type)
        case States.EDITING_POST_BUTTON_URL:
            await edit_button_url(message, state, post_message_type)
        case States.EDITING_POST_MEDIA_FILES:
            await edit_media_files(message, state, post_message_type)


@post_message_router.callback_query(
    lambda query: InlinePostMessageExtraSettingsKeyboard.callback_validator(query.data)
)
async def post_message_extra_settings_callback_handler(query: CallbackQuery):
    callback_data = InlinePostMessageExtraSettingsKeyboard.Callback.model_validate_json(query.data)

    user_id = query.from_user.id
    bot_id = callback_data.bot_id
    post_message_id = callback_data.post_message_id
    post_message_type = callback_data.post_message_type

    try:
        post_message = await get_post_message(query, user_id, bot_id, post_message_id, post_message_type)
    except PostMessageNotFound:
        return

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    if await _mailing_already_started(
            query,
            callback_data.a != callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU,
            post_message,
            custom_bot_username
    ):
        return

    match callback_data.a:
        case callback_data.ActionEnum.LINK_PREVIEW:
            await _link_preview(
                query,
                post_message,
                post_message_type,
                channel_id=callback_data.channel_id if post_message_type == PostMessageType.CHANNEL_POST else None
            )
        case callback_data.ActionEnum.NOTIFICATION_SOUND:
            await _notification_sound(
                query,
                post_message,
                post_message_type,
                channel_id=callback_data.channel_id if post_message_type == PostMessageType.CHANNEL_POST else None
            )
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(
                query,
                bot_id,
                post_message_type,
                channel_id=callback_data.channel_id if post_message_type == PostMessageType.CHANNEL_POST else None
            )


@post_message_router.callback_query(
    lambda query: InlinePostMessageStartConfirmKeyboard.callback_validator(query.data)
)
async def post_message_confirm_start_callback_handler(query: CallbackQuery):
    callback_data = InlinePostMessageStartConfirmKeyboard.Callback.model_validate_json(query.data)

    user_id = query.from_user.id
    bot_id = callback_data.bot_id
    post_message_id = callback_data.post_message_id
    post_message_type = callback_data.post_message_type

    try:
        post_message = await get_post_message(query, user_id, bot_id, post_message_id, post_message_type)
    except PostMessageNotFound:
        return

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    if await _mailing_already_started(
            query,
            callback_data.a != callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU,
            post_message,
            custom_bot_username
    ):
        return

    match callback_data.a:
        case callback_data.ActionEnum.START_CONFIRM:
            await _start_confirm(
                query,
                post_message,
                post_message_type,
                channel_id=callback_data.channel_id if post_message_type == PostMessageType.CHANNEL_POST else None
            )
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(
                query,
                bot_id,
                post_message_type,
                channel_id=callback_data.channel_id if post_message_type == PostMessageType.CHANNEL_POST else None
            )


@post_message_router.callback_query(
    lambda query: InlinePostMessageAcceptDeletingKeyboard.callback_validator(query.data)
)
async def post_message_accept_deleting_callback_handler(query: CallbackQuery):
    callback_data = InlinePostMessageAcceptDeletingKeyboard.Callback.model_validate_json(query.data)

    user_id = query.from_user.id
    bot_id = callback_data.bot_id
    post_message_id = callback_data.post_message_id
    post_message_type = callback_data.post_message_type

    try:
        post_message = await get_post_message(query, user_id, bot_id, post_message_id, post_message_type)
    except PostMessageNotFound:
        return

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    if await _mailing_already_started(
            query,
            callback_data.a != callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU,
            post_message,
            custom_bot_username
    ):
        return

    match callback_data.a:
        case callback_data.ActionEnum.ACCEPT_DELETE:
            await _delete_post_message(
                query,
                post_message,
                post_message_type,
                channel_id=callback_data.channel_id if post_message_type == PostMessageType.CHANNEL_POST else None
            )
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(
                query,
                bot_id,
                post_message_type,
                channel_id=callback_data.channel_id if post_message_type == PostMessageType.CHANNEL_POST else None
            )


async def _start_confirm(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int = None
):
    media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message.post_message_id)

    if await is_post_message_valid(query, post_message, media_files):
        if post_message.is_delayed:
            # Небольшой запас по времени
            if datetime.now() > (post_message.send_date + timedelta(minutes=1)):
                await query.answer(
                    text="Указанное время отправки уже прошло",
                    show_alert=True
                )
                return

        post_message.is_running = True
        custom_bot = await bot_db.get_bot(post_message.bot_id)

        match post_message_type:
            case PostMessageType.MAILING:
                custom_bot_username = (await Bot(custom_bot.token).get_me()).username

                await query.message.answer(
                    f"Рассылка начнется в {post_message.send_date}" if post_message.is_delayed else "Рассылка началась"
                )
                await query.message.edit_text(
                    text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                        post_message.bot_id, post_message_type, channel_id
                    ),
                    parse_mode=ParseMode.HTML
                )

                if not post_message.is_delayed:
                    await post_message_db.update_post_message(post_message)
                    await send_post_messages(
                        custom_bot,
                        post_message,
                        media_files,
                        query.from_user.id
                    )
                else:
                    job_id = await _scheduler.add_scheduled_job(
                        func=send_post_messages, run_date=post_message.send_date,
                        args=[custom_bot, post_message, media_files, query.from_user.id])
                    post_message.job_id = job_id
                    await post_message_db.update_post_message(post_message)

            case PostMessageType.CHANNEL_POST:
                channel_username = (await Bot(custom_bot.token).get_chat(channel_id)).username

                await query.message.answer(
                    f"Запись отправится в {post_message.send_date}" if post_message.is_delayed else "Запись отправлена!"
                )
                await query.message.edit_text(
                    text=MessageTexts.BOT_CHANNEL_POST_MENU_WHILE_RUNNING.value.format(channel_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                        post_message.bot_id, post_message_type, channel_id
                    ),
                    parse_mode=ParseMode.HTML
                )

                if not post_message.is_delayed:
                    await post_message_db.update_post_message(post_message)
                    await send_post_message(
                        Bot(custom_bot.token),
                        channel_id,
                        post_message,
                        media_files,
                        PostActionType.RELEASE
                    )
                else:
                    job_id = await _scheduler.add_scheduled_job(
                        func=send_post_message, run_date=post_message.send_date,
                        args=[custom_bot, channel_id, post_message, media_files, PostActionType.RELEASE])
                    post_message.job_id = job_id
                    await post_message_db.update_post_message(post_message)

            case _:
                raise UnknownPostMessageType


async def _delete_post_message(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int = None
):
    await post_message_db.delete_post_message(post_message.post_message_id)
    custom_bot = await bot_db.get_bot(post_message.bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    match post_message_type:
        case PostMessageType.MAILING:
            keyboard = await InlineBotMenuKeyboard.get_keyboard(post_message.bot_id)

            await query.message.edit_text(
                text=MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            await query.message.answer(
                text="Рассылочное сообщение удалено",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(post_message.bot_id)
            )
            await query.message.answer(
                text=MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

        case PostMessageType.CHANNEL_POST:
            channel_username = (await Bot(custom_bot.token).get_chat(channel_id)).username
            keyboard = await InlineChannelMenuKeyboard.get_keyboard(post_message.bot_id, channel_id)

            await query.message.edit_text(
                text=MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(channel_username, custom_bot_username),
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            await query.message.answer(
                text="Запись в канал удалена",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(post_message.bot_id)
            )
            await query.message.answer(
                text=MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(channel_username, custom_bot_username),
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

        case _:
            raise UnknownPostMessageType


async def _link_preview(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    post_message.enable_link_preview = not post_message.enable_link_preview
    await post_message_db.update_post_message(post_message)

    await query.message.edit_reply_markup(
        reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
            post_message.bot_id,
            post_message.post_message_id,
            post_message.enable_notification_sound,
            post_message.enable_link_preview,
            post_message_type,
            channel_id
        )
    )


async def _notification_sound(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    post_message.enable_notification_sound = not post_message.enable_notification_sound
    await post_message_db.update_post_message(post_message)

    await query.message.edit_reply_markup(
        reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
            post_message.bot_id,
            post_message.post_message_id,
            post_message.enable_notification_sound,
            post_message.enable_link_preview,
            post_message_type,
            channel_id
        )
    )


async def _mailing_already_started(
        query: CallbackQuery,
        is_callback_data_back: bool,
        post_message: PostMessageSchema,
        custom_bot_username: str
) -> bool:
    if is_callback_data_back and post_message.is_running:
        await query.answer("Рассылка уже запущена", show_alert=True)
        await query.message.edit_text(
            text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                post_message.bot_id,
                PostMessageType.MAILING,
                channel_id=None
            ),
            parse_mode=ParseMode.HTML
        )
        return True

    return False


async def _inline_back_to_post_message_menu(
        query: CallbackQuery,
        bot_id: int,
        post_message_type: PostMessageType,
        channel_id: int | None
) -> None:
    custom_bot_token = (await bot_db.get_bot(bot_id)).token

    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageType

    await query.message.edit_text(
        text=MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            bot_id, post_message_type, channel_id
        ),
        parse_mode=ParseMode.HTML
    )
