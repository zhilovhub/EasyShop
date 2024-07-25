from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.main import _scheduler
from bot.utils import MessageTexts
from bot.states import States
from bot.handlers.routers import post_message_router
from bot.keyboards.channel_keyboards import InlineChannelMenuKeyboard
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard
from bot.post_message.post_message_utils import is_post_message_valid
from bot.keyboards.post_message_keyboards import InlinePostMessageStartConfirmKeyboard, InlinePostMessageMenuKeyboard, \
    InlinePostMessageExtraSettingsKeyboard, InlinePostMessageAcceptDeletingKeyboard
from bot.post_message.post_message_editors import edit_delay_date, edit_message, edit_button_text, edit_button_url, \
    edit_media_files, send_post_message, PostActionType, edit_winners_count, edit_contest_finish_date, \
    pre_finish_contest
from bot.handlers.mailing_settings_handlers import send_post_messages
from bot.post_message.post_message_decorators import check_callback_conflicts
from bot.post_message.post_message_callback_handler import post_message_handler

from common_utils.bot_settings_config import BOT_PROPERTIES
from common_utils.keyboards.keyboards import InlineBotMenuKeyboard

from database.config import post_message_media_file_db, post_message_db, contest_db, bot_db
from database.models.post_message_model import PostMessageSchema, PostMessageType, UnknownPostMessageTypeError


from logs.config import logger, extra_params


@post_message_router.callback_query(lambda query: InlinePostMessageMenuKeyboard.callback_validator(query.data))
@check_callback_conflicts
async def post_message_menu_callback_handler(
        query: CallbackQuery,
        state: FSMContext,
        callback_data: InlinePostMessageMenuKeyboard.Callback,
        post_message: PostMessageSchema
):
    """Обрабатывает кнопки по настройки сообщения Post Message"""
    await post_message_handler(query, state, callback_data, post_message)


@post_message_router.message(StateFilter(
    States.EDITING_POST_TEXT,
    States.EDITING_POST_BUTTON_TEXT,
    States.EDITING_POST_BUTTON_URL,
    States.EDITING_POST_MEDIA_FILES,
    States.EDITING_POST_DELAY_DATE,
    States.EDITING_CONTEST_FINISH_DATE,
    States.EDITING_CONTEST_WINNERS_COUNT,
))
async def editing_post_message_handler(message: Message, state: FSMContext):
    """Обрабатывает различные состояния, отвечающие за настройки конкретных параметров сообщения"""

    state_data = await state.get_data()
    current_state = await state.get_state()

    match state_data["post_message_type"]:
        case PostMessageType.MAILING.value:
            post_message_type = PostMessageType.MAILING
        case PostMessageType.CHANNEL_POST.value:
            post_message_type = PostMessageType.CHANNEL_POST
        case PostMessageType.CONTEST.value:
            post_message_type = PostMessageType.CONTEST
        case _:
            raise UnknownPostMessageTypeError

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
        case States.EDITING_CONTEST_WINNERS_COUNT:
            await edit_winners_count(message, state, post_message_type)
        case States.EDITING_CONTEST_FINISH_DATE:
            await edit_contest_finish_date(message, state, post_message_type)


@post_message_router.callback_query(
    lambda query: InlinePostMessageExtraSettingsKeyboard.callback_validator(query.data)
)
@check_callback_conflicts
async def post_message_extra_settings_callback_handler(
        query: CallbackQuery,
        callback_data: InlinePostMessageExtraSettingsKeyboard.Callback,
        post_message: PostMessageSchema
):
    """Обрабатывает кнопки по настройки дополнительных опций Post Message"""

    bot_id = callback_data.bot_id
    post_message_type = callback_data.post_message_type

    match callback_data.a:
        case callback_data.ActionEnum.LINK_PREVIEW:
            await _link_preview(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )
        case callback_data.ActionEnum.NOTIFICATION_SOUND:
            await _notification_sound(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(
                query,
                bot_id,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )


@post_message_router.callback_query(
    lambda query: InlinePostMessageStartConfirmKeyboard.callback_validator(query.data)
)
@check_callback_conflicts
async def post_message_confirm_start_callback_handler(
        query: CallbackQuery,
        callback_data: InlinePostMessageStartConfirmKeyboard.Callback,
        post_message: PostMessageSchema
):
    """Запускает отправление Post Message"""

    bot_id = callback_data.bot_id
    post_message_type = callback_data.post_message_type

    match callback_data.a:
        case callback_data.ActionEnum.START_CONFIRM:
            await _start_confirm(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(
                query,
                bot_id,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )


@post_message_router.callback_query(
    lambda query: InlinePostMessageAcceptDeletingKeyboard.callback_validator(query.data)
)
@check_callback_conflicts
async def post_message_accept_deleting_callback_handler(
        query: CallbackQuery,
        callback_data: InlinePostMessageAcceptDeletingKeyboard.Callback,
        post_message: PostMessageSchema
):
    """Подтверждает удаление настраиваемого сообщения"""

    bot_id = callback_data.bot_id
    post_message_type = callback_data.post_message_type

    match callback_data.a:
        case callback_data.ActionEnum.ACCEPT_DELETE:
            await _delete_post_message(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(
                query,
                bot_id,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )


async def _start_confirm(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int = None
):
    """Starts sending of Post Message"""

    media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message.post_message_id)

    if await is_post_message_valid(query, post_message, post_message_type, media_files):
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
        custom_bot_username = (await Bot(custom_bot.token).get_me()).username

        match post_message_type:
            case PostMessageType.MAILING:
                await query.message.answer(
                    f"Рассылка начнется в {post_message.send_date}"
                    if post_message.is_delayed else "Рассылка началась"
                )

                if not post_message.is_delayed:
                    await post_message_db.update_post_message(post_message)
                    await query.message.edit_text(
                        text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
                        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                            post_message.bot_id, post_message_type, channel_id
                        ),
                        parse_mode=ParseMode.HTML
                    )
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

                    await query.message.edit_text(
                        text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
                        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                            post_message.bot_id, post_message_type, channel_id
                        ),
                        parse_mode=ParseMode.HTML
                    )

            case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST | PostMessageType.PARTNERSHIP_POST:
                if post_message_type == PostMessageType.CONTEST:
                    contest = await contest_db.get_contest_by_bot_id(bot_id=post_message.bot_id)
                    if contest.finish_job_id:
                        try:
                            await _scheduler.del_job(contest.finish_job_id)
                        except Exception as e:
                            logger.warning(
                                f"user_id={query.message.chat.id}: Job ID {post_message.job_id} not found",
                                extra=extra_params(
                                    user_id=query.message.chat.id,
                                    bot_id=post_message.bot_id,
                                    post_message_id=post_message.post_message_id
                                ),
                                exc_info=e
                            )

                    job_id = await _scheduler.add_scheduled_job(
                        pre_finish_contest, contest.finish_date, [contest.contest_id]
                    )
                    contest.finish_job_id = job_id
                    await contest_db.update_contest(contest)

                channel_username = (await Bot(custom_bot.token).get_chat(channel_id)).username

                await query.message.answer(
                    f"Запись отправится в {post_message.send_date}"
                    if post_message.is_delayed else "Запись отправлена!"
                )

                if not post_message.is_delayed:
                    await send_post_message(
                        Bot(custom_bot.token, default=BOT_PROPERTIES),
                        channel_id,
                        post_message,
                        media_files,
                        PostActionType.RELEASE,
                        is_delayed=False
                    )
                    if post_message_type == PostMessageType.CONTEST:
                        post_message.is_sent = True
                        await post_message_db.update_post_message(post_message)
                        await query.message.edit_text(
                            text=MessageTexts.BOT_CHANNEL_CONTEST_MENU_WHILE_RUNNING.value.format(channel_username),
                            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                                post_message.bot_id, post_message_type, channel_id
                            ),
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await post_message_db.delete_post_message(post_message.post_message_id)
                        await query.message.edit_text(
                            text=MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(
                                channel_username, custom_bot_username
                            ),
                            reply_markup=await InlineChannelMenuKeyboard.get_keyboard(
                                post_message.bot_id, channel_id
                            ),
                            parse_mode=ParseMode.HTML
                        )

                else:
                    job_id = await _scheduler.add_scheduled_job(
                        func=send_post_message, run_date=post_message.send_date,
                        args=[custom_bot, channel_id, post_message, media_files, PostActionType.RELEASE])
                    post_message.job_id = job_id
                    await post_message_db.update_post_message(post_message)

                    await query.message.edit_text(
                        text=MessageTexts.BOT_CHANNEL_POST_MENU_WHILE_RUNNING.value.format(channel_username),
                        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                            post_message.bot_id, post_message_type, channel_id
                        ),
                        parse_mode=ParseMode.HTML
                    )

            case _:
                raise UnknownPostMessageTypeError


async def _delete_post_message(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int = None
):
    """Deletes Post Message"""

    await post_message_db.delete_post_message(post_message.post_message_id)
    custom_bot = await bot_db.get_bot(post_message.bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    match post_message_type:
        case PostMessageType.MAILING:
            keyboard = await InlineBotMenuKeyboard.get_keyboard(post_message.bot_id, query.from_user.id)

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

        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST | PostMessageType.PARTNERSHIP_POST:
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
            raise UnknownPostMessageTypeError


async def _link_preview(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    """Enables/Disable link preview"""

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
    """Enables/Disable notification's sound"""

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


async def _inline_back_to_post_message_menu(
        query: CallbackQuery,
        bot_id: int,
        post_message_type: PostMessageType,
        channel_id: int | None
) -> None:
    """Returns to Post Message Menu from everywhere"""

    custom_bot_token = (await bot_db.get_bot(bot_id)).token

    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST | PostMessageType.PARTNERSHIP_POST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageTypeError

    await query.message.edit_text(
        text=MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            bot_id, post_message_type, channel_id
        ),
        parse_mode=ParseMode.HTML
    )
