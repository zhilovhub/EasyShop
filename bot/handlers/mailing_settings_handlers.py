import asyncio

from datetime import datetime, timedelta

from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.client.bot import DefaultBotProperties, Bot
from aiogram.fsm.context import FSMContext

from bot.main import bot, custom_bot_user_db, post_message_media_file_db, _scheduler, post_message_db, bot_db
from bot.utils import MessageTexts
from bot.states.states import States
from bot.handlers.routers import admin_bot_menu_router
from bot.enums.post_message_type import PostMessageType
from bot.post_message.post_message_editors import edit_button_url, PostActionType, send_post_message, \
    _is_post_message_valid, _inline_back_to_post_message_menu, \
    edit_delay_date, edit_message, edit_button_text, edit_media_files
from bot.post_message.post_message_handler import post_message_handler
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard, InlineBotMenuKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard, \
    InlinePostMessageAcceptDeletingKeyboard, InlinePostMessageExtraSettingsKeyboard, \
    InlinePostMessageStartConfirmKeyboard

from database.models.post_message_model import PostMessageNotFound

from logs.config import logger, extra_params


async def send_post_messages(custom_bot, post_message, media_files, chat_id):
    post_message_id = post_message.post_message_id
    all_custom_bot_users = await custom_bot_user_db.get_custom_bot_users(custom_bot.bot_id)
    custom_bot_tg = Bot(custom_bot.token, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML))

    for ind, user in enumerate(all_custom_bot_users, start=1):
        post_message = await post_message_db.get_post_message(post_message_id)

        if not post_message.is_running:
            post_message.sent_post_message_amount = 0
            await post_message_db.update_post_message(post_message)
            return

        await send_post_message(
            bot_from_send=custom_bot_tg,
            to_user_id=user.user_id,
            post_message_schema=post_message,
            media_files=media_files,
            post_action_type=PostActionType.RELEASE,
            message=None,
        )

        logger.info(
            f"post_message with post_message_id {post_message_id} has "
            f"sent to {ind}/{len(all_custom_bot_users)} with user_id {user.user_id}"
        )
        # 20 messages per second (limit is 30)
        await asyncio.sleep(.05)
        post_message.sent_post_message_amount += 1
        await post_message_db.update_post_message(post_message)

    await bot.send_message(
        chat_id,
        f"Рассылка завершена\nСообщений отправлено - "
        f"{post_message.sent_post_message_amount}/{len(all_custom_bot_users)}"
    )

    post_message.is_running = False
    post_message.sent_post_message_amount = 0

    await post_message_db.delete_post_message(post_message.post_message_id)
    # await asyncio.sleep(10) # For test only


@admin_bot_menu_router.callback_query(lambda query: InlinePostMessageMenuKeyboard.callback_validator(query.data))
async def mailing_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    await post_message_handler(query, state)


@admin_bot_menu_router.callback_query(
    lambda query: InlinePostMessageAcceptDeletingKeyboard.callback_validator(query.data)
)
async def mailing_accept_deleting_callback_handler(query: CallbackQuery):
    callback_data = InlinePostMessageAcceptDeletingKeyboard.Callback.model_validate_json(query.data)

    user_id = query.from_user.id
    post_message_id = callback_data.post_message_id
    bot_id = callback_data.bot_id

    try:
        post_message = await post_message_db.get_post_message(post_message_id)
    except PostMessageNotFound:
        logger.info(
            f"user_id={user_id}: tried to edit post_message_id={post_message_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_id=bot_id, post_message_id=post_message_id)
        )
        await query.answer("Рассылка уже завершена или удалена", show_alert=True)
        await query.message.delete()
        return

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    if callback_data.a != callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU and post_message.is_running:
        await query.answer("Рассылка уже запущена", show_alert=True)
        await query.message.edit_text(
            text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                bot_id, PostMessageType.MAILING
            ),
            parse_mode=ParseMode.HTML
        )
        return

    match callback_data.a:
        case callback_data.ActionEnum.ACCEPT_DELETE:
            await post_message_db.delete_post_message(post_message_id)

            keyboard = await InlineBotMenuKeyboard.get_keyboard(bot_id)
            await query.message.edit_text(
                text=MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            await query.message.answer(
                text="Рассылочное сообщение удалено",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            await query.message.answer(
                text=MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(query, bot_id, custom_bot_username, post_message_type)


@admin_bot_menu_router.callback_query(
    lambda query: InlinePostMessageExtraSettingsKeyboard.callback_validator(query.data)
)
async def mailing_extra_settings_callback_handler(query: CallbackQuery):
    callback_data = InlinePostMessageExtraSettingsKeyboard.Callback.model_validate_json(query.data)

    user_id = query.from_user.id
    post_message_id = callback_data.post_message_id
    bot_id = callback_data.bot_id

    try:
        post_message = await post_message_db.get_post_message(post_message_id)
    except PostMessageNotFound:
        logger.info(
            f"user_id={user_id}: tried to edit post_message_id={post_message_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_id=bot_id, post_message_id=post_message_id)
        )
        await query.answer("Рассылка уже завершена или удалена", show_alert=True)
        await query.message.delete()
        return

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    if callback_data.a != callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU and post_message.is_running:
        await query.answer("Рассылка уже запущена", show_alert=True)
        await query.message.edit_text(
            text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, PostMessageType.MAILING),
            parse_mode=ParseMode.HTML
        )
        return

    match callback_data.a:
        case callback_data.ActionEnum.LINK_PREVIEW:
            post_message.enable_link_preview = not post_message.enable_link_preview
            await post_message_db.update_post_message(post_message)

            await query.message.edit_reply_markup(
                reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
                    bot_id,
                    post_message_id,
                    post_message.enable_notification_sound,
                    post_message.enable_link_preview
                )
            )
        case callback_data.ActionEnum.NOTIFICATION_SOUND:
            post_message.enable_notification_sound = not post_message.enable_notification_sound
            await post_message_db.update_post_message(post_message)

            await query.message.edit_reply_markup(
                reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
                    bot_id,
                    post_message_id,
                    post_message.enable_notification_sound,
                    post_message.enable_link_preview
                )
            )
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(query, bot_id, custom_bot_username, post_message_type)


@admin_bot_menu_router.callback_query(
    lambda query: InlinePostMessageStartConfirmKeyboard.callback_validator(query.data)
)
async def mailing_confirm_start_callback_handler(query: CallbackQuery):
    callback_data = InlinePostMessageStartConfirmKeyboard.Callback.model_validate_json(query.data)

    user_id = query.from_user.id
    post_message_id = callback_data.post_message_id
    bot_id = callback_data.bot_id

    try:
        post_message = await post_message_db.get_post_message(post_message_id)
    except PostMessageNotFound:
        logger.info(
            f"user_id={user_id}: tried to edit post_message_id={post_message_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_id=bot_id, post_message_id=post_message_id)
        )
        await query.answer("Рассылка уже завершена или удалена", show_alert=True)
        await query.message.delete()
        return

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    if callback_data.a != callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU and post_message.is_running:
        await query.answer("Рассылка уже запущена", show_alert=True)
        await query.message.edit_text(
            text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, PostMessageType.MAILING),
            parse_mode=ParseMode.HTML
        )
        return

    match callback_data.a:
        case callback_data.ActionEnum.START_CONFIRM:
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

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

                await query.message.answer(
                    f"Рассылка начнется в {post_message.send_date}" if post_message.is_delayed else "Рассылка началась"
                )
                await query.message.edit_text(
                    text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, PostMessageType.MAILING),
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

        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(query, bot_id, custom_bot_username, post_message_type)


@admin_bot_menu_router.message(StateFilter(
    States.EDITING_MAILING_DELAY_DATE,
    States.EDITING_MAILING_MESSAGE,
    States.EDITING_MAILING_BUTTON_TEXT,
    States.EDITING_MAILING_BUTTON_URL,
    States.EDITING_MAILING_MEDIA_FILES,
))
async def editing_post_message_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()

    match current_state:
        case States.EDITING_MAILING_DELAY_DATE:
            await edit_delay_date(message, state, PostMessageType.MAILING)
        case States.EDITING_MAILING_MESSAGE:
            await edit_message(message, state, PostMessageType.MAILING)
        case States.EDITING_MAILING_BUTTON_TEXT:
            await edit_button_text(message, state, PostMessageType.MAILING)
        case States.EDITING_MAILING_BUTTON_URL:
            await edit_button_url(message, state, PostMessageType.MAILING)
        case States.EDITING_MAILING_MEDIA_FILES:
            await edit_media_files(message, state, PostMessageType.MAILING)
