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
from bot.keyboards.main_menu_keyboards import InlineBotMenuKeyboard, ReplyBotMenuKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageStartConfirmKeyboard, InlinePostMessageMenuKeyboard, \
    InlinePostMessageExtraSettingsKeyboard, InlinePostMessageAcceptDeletingKeyboard, UnknownPostMessageType
from bot.post_message.post_message_editors import edit_delay_date, edit_message, edit_button_text, edit_button_url, \
    edit_media_files, _is_post_message_valid, _inline_back_to_post_message_menu
from bot.handlers.mailing_settings_handlers import send_post_messages
from bot.post_message.post_message_callback_handler import post_message_handler

from database.models.post_message_model import PostMessageNotFound, PostMessageSchema

from logs.config import logger, extra_params


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
        post_message = await _get_post_message(query, user_id, bot_id, post_message_id, post_message_type)
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
            await _link_preview(query, post_message, post_message_type)
        case callback_data.ActionEnum.NOTIFICATION_SOUND:
            await _notification_sound(query, post_message, post_message_type)
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(query, bot_id, custom_bot_username, post_message_type)


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
        post_message = await _get_post_message(query, user_id, bot_id, post_message_id, post_message_type)
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
            await _start_confirm(query, post_message, post_message_type)
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(query, bot_id, custom_bot_username, post_message_type)


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
        post_message = await _get_post_message(query, user_id, bot_id, post_message_id, post_message_type)
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
            await _delete_post_message(query, post_message, post_message_type)
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(query, bot_id, custom_bot_username, post_message_type)


async def _start_confirm(query: CallbackQuery, post_message: PostMessageSchema, post_message_type: PostMessageType):
    media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message.post_message_id)

    if await _is_post_message_valid(query, post_message, media_files):
        if post_message.is_delayed:
            # Небольшой запас по времени
            if datetime.now() > (post_message.send_date + timedelta(minutes=1)):
                await query.answer(
                    text="Указанное время отправки уже прошло",
                    show_alert=True
                )
                return

        post_message.is_running = True

        match post_message_type:
            case PostMessageType.MAILING:
                custom_bot = await bot_db.get_bot(post_message.bot_id)
                custom_bot_username = (await Bot(custom_bot.token).get_me()).username

                await query.message.answer(
                    f"Рассылка начнется в {post_message.send_date}" if post_message.is_delayed else "Рассылка началась"
                )
                await query.message.edit_text(
                    text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                        post_message.bot_id, post_message_type
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
                raise Exception("TODO")  # TODO

            case _:
                raise UnknownPostMessageType


async def _delete_post_message(
        query: CallbackQuery,
        post_message:
        PostMessageSchema,
        post_message_type: PostMessageType
):
    await post_message_db.delete_post_message(post_message.post_message_id)

    match post_message_type:
        case PostMessageType.MAILING:
            custom_bot = await bot_db.get_bot(post_message.bot_id)
            custom_bot_username = (await Bot(custom_bot.token).get_me()).username

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
            raise Exception("TODO")  # TODO

        case _:
            raise UnknownPostMessageType


async def _link_preview(query: CallbackQuery, post_message: PostMessageSchema, post_message_type: PostMessageType):
    post_message.enable_link_preview = not post_message.enable_link_preview
    await post_message_db.update_post_message(post_message)

    await query.message.edit_reply_markup(
        reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
            post_message.bot_id,
            post_message.post_message_id,
            post_message.enable_notification_sound,
            post_message.enable_link_preview,
            post_message_type
        )
    )


async def _notification_sound(
        query: CallbackQuery,
        post_message:
        PostMessageSchema,
        post_message_type: PostMessageType
):
    post_message.enable_notification_sound = not post_message.enable_notification_sound
    await post_message_db.update_post_message(post_message)

    await query.message.edit_reply_markup(
        reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
            post_message.bot_id,
            post_message.post_message_id,
            post_message.enable_notification_sound,
            post_message.enable_link_preview,
            post_message_type
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
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(post_message.bot_id, PostMessageType.MAILING),
            parse_mode=ParseMode.HTML
        )
        return True

    return False


async def _get_post_message(
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
        await query.message.delete()

        match post_message_type:
            case PostMessageType.MAILING:
                await query.answer("Рассылка уже завершена или удалена", show_alert=True)
            case PostMessageType.CHANNEL_POST:
                await query.answer("Запись в канал уже отправлена или удалена", show_alert=True)
            case _:
                raise UnknownPostMessageType

        raise e
