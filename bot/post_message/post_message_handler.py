from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.main import bot_db, post_message_db, bot, post_message_media_file_db, custom_bot_user_db, _scheduler
from bot.utils import MessageTexts
from bot.config import WEB_APP_URL, WEB_APP_PORT
from bot.states import States
from bot.enums.post_message_type import PostMessageType
from bot.keyboards.channel_keyboards import InlineChannelMenuKeyboard
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard, InlineBotMenuKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard, ReplyBackPostMessageMenuKeyboard, \
    ReplyConfirmMediaFilesKeyboard, InlinePostMessageAcceptDeletingKeyboard, InlinePostMessageExtraSettingsKeyboard, \
    InlinePostMessageStartConfirmKeyboard
from bot.post_message.post_message_editors import _inline_no_button, _is_post_message_valid, send_post_message, \
    PostActionType

from database.models.post_message_model import PostMessageSchema, PostMessageNotFound

from logs.config import extra_params, logger


async def _post_message_mailing(
        query: CallbackQuery,
        state: FSMContext,
        callback_data: InlinePostMessageMenuKeyboard.Callback,
        user_id: int,
        bot_id: int,
        post_message: PostMessageSchema,
        custom_bot_username: str
):
    match callback_data.a:
        # RUNNING ACTIONS
        case callback_data.ActionEnum.STATISTICS:
            custom_users_length = len(await custom_bot_user_db.get_custom_bot_users(bot_id=bot_id))

            await query.answer(
                text=f"Отправлено {post_message.sent_post_message_amount}/{custom_users_length} сообщений",
                show_alert=True
            )


async def _post_message_channel_post(
        query: CallbackQuery,
        state: FSMContext,
        callback_data: InlinePostMessageMenuKeyboard.Callback,
        user_id: int,
        bot_id: int,
        post_message: PostMessageSchema,
        channel_username: str
):
    pass


async def _post_message_union(
        query: CallbackQuery,
        state: FSMContext,
        callback_data: InlinePostMessageMenuKeyboard.Callback,
        user_id: int,
        bot_id: int,
        channel_id: int,
        post_message: PostMessageSchema,
        username: str,
        post_message_type: PostMessageType):
    post_message_id = post_message.post_message_id

    match callback_data.a:
        # RUNNING ACTIONS
        case callback_data.ActionEnum.CANCEL:
            custom_users_length = len(await custom_bot_user_db.get_custom_bot_users(bot_id=bot_id))

            post_message.is_running = False

            try:
                await _scheduler.del_job_by_id(post_message.job_id)
            except Exception as e:
                logger.warning(
                    f"user_id={user_id}: Job ID {post_message.job_id} not found",
                    extra=extra_params(user_id=user_id, bot_id=bot_id, post_message_id=post_message_id),
                    exc_info=e
                )

            post_message.job_id = None

            await post_message_db.delete_post_message(post_message.post_message_id)

            match post_message_type:
                case PostMessageType.MAILING:
                    await query.message.answer(
                        f"Рассылка остановлена\nСообщений разослано - "
                        f"{post_message.sent_post_message_amount}/{custom_users_length}",
                        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
                    )
                    await query.message.edit_text(
                        MessageTexts.BOT_MENU_MESSAGE.value.format(username),
                        reply_markup=await InlineBotMenuKeyboard.get_keyboard(bot_id),
                        parse_mode=ParseMode.HTML
                    )
                case PostMessageType.CHANNEL_POST:
                    await query.message.answer(
                        f"Отправка записи отменена",
                        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
                    )
                    await query.message.edit_text(
                        MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(username),
                        reply_markup=await InlineChannelMenuKeyboard.get_keyboard(bot_id, channel_id),
                        parse_mode=ParseMode.HTML
                    )

        # NOT RUNNING ACTIONS
        case callback_data.ActionEnum.BUTTON_ADD:
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

            if post_message.has_button:
                await query.answer(MessageTexts.bot_post_already_done_message(post_message_type), show_alert=True)
                await query.message.edit_text(
                    text=MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type),
                    parse_mode=ParseMode.HTML
                )
            elif len(media_files) > 1:
                await query.answer(
                    "Кнопку нельзя добавить, если в сообщении больше одного медиафайла",
                    show_alert=True
                )
            else:
                post_message.button_text = "Shop"
                post_message.button_url = f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id={bot_id}"  # TODO ?
                post_message.has_button = True

                await post_message_db.update_post_message(post_message)

                await query.message.delete()
                await query.message.answer(
                    "Кнопка добавлена\n\n"
                    f"Сейчас там стандартный текст '{post_message.button_text}' и ссылка на Ваш магазин.\n"
                    "Эти два параметры Вы можете изменить в настройках рассылки"
                )

                await query.message.answer(
                    text=MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type)
                )

        case callback_data.ActionEnum.BUTTON_URL:
            if not post_message.has_button:
                await _inline_no_button(query, bot_id, username)
            else:
                await query.message.answer(
                    "Введите ссылку, которая будет открываться у пользователей по нажатии на кнопку",
                    reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
                )
                await query.answer()
                await state.set_state(States.EDITING_MAILING_BUTTON_URL)  # TODO 1
                await state.set_data({"bot_id": bot_id, "post_message_id": post_message_id})

        case callback_data.ActionEnum.BUTTON_TEXT:
            if not post_message.has_button:
                await _inline_no_button(query, bot_id, username)
            else:
                await query.message.answer(
                    "Введите текст, который будет отображаться на кнопке",
                    reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
                )
                await query.answer()
                await state.set_state(States.EDITING_MAILING_BUTTON_TEXT)  # TODO 1
                await state.set_data({"bot_id": bot_id, "post_message_id": post_message_id})

        case callback_data.ActionEnum.BUTTON_DELETE:
            if not post_message.has_button:
                await _inline_no_button(query, bot_id, username)
            else:
                post_message.button_text = None
                post_message.button_url = None
                post_message.has_button = False

                await post_message_db.update_post_message(post_message)

                await query.message.delete()
                await query.message.answer("Кнопка удалена")
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(username),  # TODO 1
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type)
                )

        case callback_data.ActionEnum.POST_MESSAGE_TEXT:
            await query.message.answer(
                "Введите текст, который будет отображаться в рассылочном сообщении",  # TODO 1
                reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.EDITING_MAILING_MESSAGE)  # TODO 1
            await state.set_data({"bot_id": bot_id, "post_message_id": post_message_id})

        case callback_data.ActionEnum.POST_MESSAGE_MEDIA:
            await query.message.answer(
                "Отправьте одним сообщение медиафайлы для рассылочного сообщения\n\n"  # TODO 1
                "❗ Старые медиафайлы к этому рассылочному сообщению <b>перезапишутся</b>\n\n"
                "❗❗ Обратите внимание, что к сообщению нельзя будет прикрепить кнопку, "
                "если медиафайлов <b>больше одного</b>",
                reply_markup=ReplyConfirmMediaFilesKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.EDITING_MAILING_MEDIA_FILES)  # TODO 1
            await state.set_data({"bot_id": bot_id, "post_message_id": post_message_id})

        case callback_data.ActionEnum.START:
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

            if await _is_post_message_valid(query, post_message, media_files):
                await query.message.edit_text(
                    text=MessageTexts.BOT_MAILINGS_MENU_ACCEPT_START.value.format(username),  # TODO 1
                    reply_markup=InlinePostMessageStartConfirmKeyboard.get_keyboard(bot_id, post_message_id)
                )

        case callback_data.ActionEnum.DEMO:
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

            if await _is_post_message_valid(query, post_message, media_files):
                await send_post_message(
                    bot,
                    query.from_user.id,
                    post_message,
                    media_files,
                    PostActionType.DEMO,
                    PostMessageType.MAILING,
                    query.message
                )
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(username),  # TODO 1
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type)
                )

        case callback_data.ActionEnum.DELETE_POST_MESSAGE:
            await query.message.edit_text(
                text=MessageTexts.BOT_MAILINGS_MENU_ACCEPT_DELETING_MESSAGE.value.format(username),  # TODO 1
                reply_markup=await InlinePostMessageAcceptDeletingKeyboard.get_keyboard(bot_id, post_message_id)
            )

        case callback_data.ActionEnum.EXTRA_SETTINGS:
            await query.message.edit_text(
                text=query.message.html_text + "\n\n🔎 Что такое <a href=\"https://www.google.com/url?sa=i&url=https%3A"
                                               "%2F%2Ftlgrm.ru%2Fblog%2Flink-preview.html&psig=AOvVaw27FhHb7fFrLDNGUX-u"
                                               "zG7y&ust=1717771529744000&source=images&cd=vfe&opi=89978449&ved=0CBIQjR"
                                               "xqFwoTCJj5puKbx4YDFQAAAAAdAAAAABAE\">предпросмотр ссылок</a>",
                reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
                    bot_id,
                    post_message_id,
                    post_message.enable_notification_sound,
                    post_message.enable_link_preview
                ),
                parse_mode=ParseMode.HTML,
            )

        case callback_data.ActionEnum.DELAY:
            await query.message.answer(
                MessageTexts.DATE_RULES.value,
                reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.EDITING_MAILING_DELAY_DATE)
            await state.set_data({"bot_id": bot_id, "post_message_id": post_message_id})

        case callback_data.ActionEnum.REMOVE_DELAY:
            post_message.is_delayed = False
            post_message.send_date = None

            await post_message_db.update_post_message(post_message)

            await query.message.edit_reply_markup(
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type)
            )

        case callback_data.ActionEnum.BACK_TO_MAIN_MENU:
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id),
                parse_mode=ParseMode.HTML
            )


async def post_message_handler(query: CallbackQuery, state: FSMContext):
    callback_data = InlinePostMessageMenuKeyboard.Callback.model_validate_json(query.data)

    post_message_type = callback_data.post_message_type
    user_id = query.from_user.id
    post_message_id = callback_data.post_message_id
    bot_id = callback_data.bot_id
    channel_id = callback_data.channel_id  # TODO get channel_id (there is no it right now)

    try:
        post_message = await post_message_db.get_post_message(post_message_id)
    except PostMessageNotFound:
        logger.info(
            f"user_id={user_id}: tried to edit post_message_id={post_message_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_id=bot_id, post_message_id=post_message_id)
        )
        await query.answer(MessageTexts.bot_post_already_done_message(post_message_type), show_alert=True)
        await query.message.delete()
        return

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    if not custom_bot_username:
        username = (await custom_bot.get_chat(channel_id)).username
    else:
        username = custom_bot_username

    if callback_data.a not in (
            callback_data.ActionEnum.STATISTICS,
            callback_data.ActionEnum.CANCEL,
            callback_data.ActionEnum.BACK_TO_MAIN_MENU
    ) and post_message.is_running:
        await query.answer(MessageTexts.bot_post_already_started_message(post_message_type), show_alert=True)
        await query.message.edit_text(
            text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type),
            parse_mode=ParseMode.HTML
        )
        return

    match post_message_type:
        case PostMessageType.MAILING:  # specific buttons for mailing
            await _post_message_mailing(query, state, callback_data, user_id, bot_id, post_message, custom_bot_username)
        case PostMessageType.CHANNEL_POST:  # specific buttons for channel post
            await _post_message_channel_post(query, state, )

    # union buttons for mailing and channel post
    await _post_message_union(
        query,
        state,
        callback_data,
        user_id,
        bot_id,
        channel_id,
        post_message,
        custom_bot_username,  # TODO what about channel username
        post_message_type
    )
