import asyncio

from datetime import datetime, timedelta

from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.client.bot import DefaultBotProperties, Bot
from aiogram.fsm.context import FSMContext

from bot.main import bot, custom_bot_user_db, post_message_media_file_db, _scheduler, post_message_db, bot_db
from bot.utils import MessageTexts
from bot.config import WEB_APP_URL, WEB_APP_PORT
from bot.states.states import States
from bot.handlers.routers import admin_bot_menu_router
from bot.utils.post_message import edit_button_url, PostMessageType, PostActionType, send_post_message, \
    _inline_no_button, _is_post_message_valid, _inline_back_to_post_message_menu, _back_to_post_message_menu, \
    _reply_no_button
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard, InlineBotMenuKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard, ReplyBackPostMessageMenuKeyboard, \
    InlinePostMessageAcceptDeletingKeyboard, ReplyConfirmMediaFilesKeyboard, InlinePostMessageExtraSettingsKeyboard, \
    InlinePostMessageStartConfirmKeyboard

from database.models.post_message_model import PostMessageNotFound
from database.models.post_message_media_files import PostMessageMediaFileSchema

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
    callback_data = InlinePostMessageMenuKeyboard.Callback.model_validate_json(query.data)

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

    if callback_data.a not in (
            callback_data.ActionEnum.STATISTICS,
            callback_data.ActionEnum.CANCEL,
            callback_data.ActionEnum.BACK_TO_MAIN_MENU
    ) and post_message.is_running:
        await query.answer("Рассылка уже запущена", show_alert=True)
        await query.message.edit_text(
            text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
            parse_mode=ParseMode.HTML
        )
        return

    match callback_data.a:
        # RUNNING ACTIONS
        case callback_data.ActionEnum.STATISTICS:
            custom_users_length = len(await custom_bot_user_db.get_custom_bot_users(bot_id=bot_id))

            await query.answer(
                text=f"Отправлено {post_message.sent_post_message_amount}/{custom_users_length} сообщений",
                show_alert=True
            )
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

            await query.message.answer(
                f"Рассылка остановлена\nСообщений разослано - "
                f"{post_message.sent_post_message_amount}/{custom_users_length}",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(bot_id),
                parse_mode=ParseMode.HTML
            )

        # NOT RUNNING ACTIONS
        case callback_data.ActionEnum.BUTTON_ADD:
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

            if post_message.has_button:
                await query.answer("В рассылочном сообщении кнопка уже есть", show_alert=True)
                await query.message.edit_text(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
                    parse_mode=ParseMode.HTML
                )
            elif len(media_files) > 1:
                await query.answer(
                    "Кнопку нельзя добавить, если в сообщении больше одного медиафайла",
                    show_alert=True
                )
            else:
                post_message.button_text = "Shop"
                post_message.button_url = f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id={bot_id}"
                post_message.has_button = True

                await post_message_db.update_post_message(post_message)

                await query.message.delete()
                await query.message.answer(
                    "Кнопка добавлена\n\n"
                    f"Сейчас там стандартный текст '{post_message.button_text}' и ссылка на Ваш магазин.\n"
                    "Эти два параметры Вы можете изменить в настройках рассылки"
                )
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
                )
        case callback_data.ActionEnum.BUTTON_URL:
            if not post_message.has_button:
                await _inline_no_button(query, bot_id, custom_bot_username)
            else:
                await query.message.answer(
                    "Введите ссылку, которая будет открываться у пользователей по нажатии на кнопку",
                    reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
                )
                await query.answer()
                await state.set_state(States.EDITING_MAILING_BUTTON_URL)
                await state.set_data({"bot_id": bot_id, "post_message_id": post_message_id})
        case callback_data.ActionEnum.BUTTON_TEXT:
            if not post_message.has_button:
                await _inline_no_button(query, bot_id, custom_bot_username)
            else:
                await query.message.answer(
                    "Введите текст, который будет отображаться на кнопке",
                    reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
                )
                await query.answer()
                await state.set_state(States.EDITING_MAILING_BUTTON_TEXT)
                await state.set_data({"bot_id": bot_id, "post_message_id": post_message_id})
        case callback_data.ActionEnum.BUTTON_DELETE:
            if not post_message.has_button:
                await _inline_no_button(query, bot_id, custom_bot_username)
            else:
                post_message.button_text = None
                post_message.button_url = None
                post_message.has_button = False

                await post_message_db.update_post_message(post_message)

                await query.message.delete()
                await query.message.answer("Кнопка удалена")
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
                )
        case callback_data.ActionEnum.POST_MESSAGE_TEXT:
            await query.message.answer(
                "Введите текст, который будет отображаться в рассылочном сообщении",
                reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.EDITING_MAILING_MESSAGE)
            await state.set_data({"bot_id": bot_id, "post_message_id": post_message_id})
        case callback_data.ActionEnum.POST_MESSAGE_MEDIA:
            await query.message.answer(
                "Отправьте одним сообщение медиафайлы для рассылочного сообщения\n\n"
                "❗ Старые медиафайлы к этому рассылочному сообщению <b>перезапишутся</b>\n\n"
                "❗❗ Обратите внимание, что к сообщению нельзя будет прикрепить кнопку, "
                "если медиафайлов <b>больше одного</b>",
                reply_markup=ReplyConfirmMediaFilesKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.EDITING_MAILING_MEDIA_FILES)
            await state.set_data({"bot_id": bot_id, "post_message_id": post_message_id})
        case callback_data.ActionEnum.START:
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

            if await _is_post_message_valid(query, post_message, media_files):
                await query.message.edit_text(
                    text=MessageTexts.BOT_MAILINGS_MENU_ACCEPT_START.value.format(custom_bot_username),
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
                    query.message
                )
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
                )
        case callback_data.ActionEnum.DELETE_POST_MESSAGE:
            await query.message.edit_text(
                text=MessageTexts.BOT_MAILINGS_MENU_ACCEPT_DELETING_MESSAGE.value.format(custom_bot_username),
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
            await state.set_state(States.EDITING_DELAY_DATE)
            await state.set_data({"bot_id": bot_id, "post_message_id": post_message_id})

        case callback_data.ActionEnum.REMOVE_DELAY:
            post_message.is_delayed = False
            post_message.send_date = None

            await post_message_db.update_post_message(post_message)

            await query.message.edit_reply_markup(
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
            )
        case callback_data.ActionEnum.BACK_TO_MAIN_MENU:
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id),
                parse_mode=ParseMode.HTML
            )


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
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
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
            await _inline_back_to_post_message_menu(query, bot_id, custom_bot_username)


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
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
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
            await _inline_back_to_post_message_menu(query, bot_id, custom_bot_username)


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
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
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

                await query.message.answer(
                    f"Рассылка начнется в {post_message.send_date}" if post_message.is_delayed else "Рассылка началась"
                )
                await query.message.edit_text(
                    text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
                    parse_mode=ParseMode.HTML
                )
        case callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU:
            await _inline_back_to_post_message_menu(query, bot_id, custom_bot_username)


@admin_bot_menu_router.message(States.EDITING_DELAY_DATE)
async def editing_mailing_delay_date_handler(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    post_message = await post_message_db.get_post_message(post_message_id)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username)
        else:
            try:
                datetime_obj = datetime.strptime(message_text, "%d.%m.%Y %H:%M")
                datetime_obj.replace(tzinfo=None)

                if datetime.now() > datetime_obj:
                    return await message.reply("Введенное время уже прошло. Введите, пожалуйста, <b>будущее</b> время")

                post_message.is_delayed = True
                post_message.send_date = datetime_obj

                await post_message_db.update_post_message(post_message)

                await message.reply(
                    f"Запланировано на: <b>{datetime_obj.strftime('%Y-%m-%d %H:%M')}</b>\n\n"
                    f"Для запуска отложенной рассылки в меню нажмите <b>Запустить</b>",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
                )
                await message.answer(
                    MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
                )
            except ValueError:
                return await message.reply("Некорректный формат. Пожалуйста, "
                                           "введите время и дату в правильном формате."
                                           )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})


@admin_bot_menu_router.message(States.EDITING_MAILING_MESSAGE)
async def editing_mailing_message_handler(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    post_message = await post_message_db.get_post_message(post_message_id)
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username)
        else:
            post_message.description = message.html_text
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

            await post_message_db.update_post_message(post_message)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            await send_post_message(
                bot,
                message.from_user.id,
                post_message,
                media_files,
                PostActionType.AFTER_REDACTING,
                message,
            )
            await message.answer(
                MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})
    else:
        await message.answer(
            "Описание должно содержать текст.\n"
            "Если есть необходимость прикрепить медиафайлы, то для этого есть пункт в меню"
        )


@admin_bot_menu_router.message(States.EDITING_MAILING_BUTTON_TEXT)
async def editing_mailing_button_text_handler(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    post_message = await post_message_db.get_post_message(post_message_id)
    if not post_message.has_button:
        return await _reply_no_button(message, bot_id, custom_bot_username, state, PostMessageType.MAILING)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username)
        else:
            post_message.button_text = message.text
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)
            await post_message_db.update_post_message(post_message)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
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
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})
    else:
        await message.answer("Название кнопки должно содержать текст")


@admin_bot_menu_router.message(States.EDITING_MAILING_BUTTON_URL)
async def editing_mailing_button_url_handler(message: Message, state: FSMContext):
    await edit_button_url(message, state, PostMessageType.MAILING)


@admin_bot_menu_router.message(States.EDITING_MAILING_MEDIA_FILES)
async def editing_mailing_media_files_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    if (message.photo or message.video or message.audio or message.document) and "first" not in state_data:
        await post_message_media_file_db.delete_post_message_media_files(post_message_id)
        state_data["first"] = True

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    match message.text:
        case ReplyConfirmMediaFilesKeyboard.Callback.ActionEnum.CONFIRM.value:
            return await _back_to_post_message_menu(message, bot_id, custom_bot_username)
        case ReplyConfirmMediaFilesKeyboard.Callback.ActionEnum.CLEAR.value:
            await message.answer("Очищаем все файлы...")
            await post_message_media_file_db.delete_post_message_media_files(post_message_id=post_message_id)
            return await message.answer(
                "Отправьте одним сообщение медиафайлы для рассылочного сообщения\n\n"
                "❗ Старые медиафайлы к этому рассылочному сообщению <b>перезапишутся</b>\n\n"
                "❗❗ Обратите внимание, что к сообщению нельзя будет прикрепить кнопку, "
                "если медиафайлов <b>больше одного</b>",
                reply_markup=ReplyConfirmMediaFilesKeyboard.get_keyboard()
            )
        case _:
            if message.photo:
                photo = message.photo[-1]
                file_id = photo.file_id
                file_path = (await bot.get_file(photo.file_id)).file_path
                media_type = "photo"
                answer_text = f"Фото {photo.file_unique_id} добавлено"
            elif message.video:
                video = message.video
                file_id = video.file_id
                file_path = (await bot.get_file(video.file_id)).file_path
                media_type = "video"
                answer_text = f"Видео {video.file_name} добавлено"
            elif message.audio:
                audio = message.audio
                file_id = audio.file_id
                file_path = (await bot.get_file(audio.file_id)).file_path
                media_type = "audio"
                answer_text = f"Аудио {audio.file_name} добавлено"
            elif message.document:
                document = message.document
                file_id = document.file_id
                file_path = (await bot.get_file(document.file_id)).file_path
                media_type = "document"
                answer_text = f"Документ {document.file_name} добавлен"
            else:
                return await message.answer(
                    "Пришлите медиафайлы (фото, видео, аудио, документы), "
                    "которые должны быть прикреплены к рассылочному сообщению",
                    reply_markup=ReplyConfirmMediaFilesKeyboard.get_keyboard()
                )

    await post_message_media_file_db.add_post_message_media_file(PostMessageMediaFileSchema.model_validate(
        {"post_message_id": post_message_id, "file_id_main_bot": file_id,
         "file_path": file_path, "media_type": media_type}
    ))

    await message.answer(answer_text)
