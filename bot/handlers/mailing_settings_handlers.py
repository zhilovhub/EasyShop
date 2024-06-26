import asyncio
import re

from enum import Enum
from datetime import datetime, timedelta

from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, LinkPreviewOptions, \
    InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument, BufferedInputFile, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.client.bot import DefaultBotProperties, Bot
from aiogram.fsm.context import FSMContext

from bot.main import bot, custom_bot_user_db, mailing_media_file_db, _scheduler, mailing_db, bot_db
from bot.utils import MessageTexts
from bot.config import WEB_APP_URL, WEB_APP_PORT
from bot.states.states import States
from bot.handlers.routers import admin_bot_menu_router
from bot.utils.keyboard_utils import make_webapp_info
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard, InlineBotMenuKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard, ReplyBackPostMessageMenuKeyboard, \
    InlinePostMessageAcceptDeletingKeyboard, ReplyConfirmMediaFilesKeyboard, InlinePostMessageExtraSettingsKeyboard, \
    InlinePostMessageStartConfirmKeyboard

from database.models.mailing_model import MailingNotFound, MailingSchema
from database.models.mailing_media_files import MailingMediaFileSchema

from logs.config import logger, extra_params


class MailingMessageType(Enum):
    DEMO = "demo"  # Демо сообщение с главного бота
    # Демо сообщение с главного бота (но немного другой функионал для отправки)
    AFTER_REDACTING = "after_redacting"
    # Главная рассылка (отправка с кастомного бота всем пользователям)
    RELEASE = "release"


async def send_mailing_messages(custom_bot, mailing, media_files, chat_id):
    mailing_id = mailing.mailing_id
    all_custom_bot_users = await custom_bot_user_db.get_custom_bot_users(custom_bot.bot_id)
    custom_bot_tg = Bot(custom_bot.token, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML))

    for ind, user in enumerate(all_custom_bot_users, start=1):
        mailing = await mailing_db.get_mailing(mailing_id)

        if not mailing.is_running:
            mailing.sent_mailing_amount = 0
            await mailing_db.update_mailing(mailing)
            return

        await send_mailing_message(
            bot_from_send=custom_bot_tg,
            to_user_id=user.user_id,
            mailing_schema=mailing,
            media_files=media_files,
            mailing_message_type=MailingMessageType.RELEASE,
            message=None,
        )

        logger.info(
            f"mailing with mailing_id {mailing_id} has "
            f"sent to {ind}/{len(all_custom_bot_users)} with user_id {user.user_id}"
        )
        # 20 messages per second (limit is 30)
        await asyncio.sleep(.05)
        mailing.sent_mailing_amount += 1
        await mailing_db.update_mailing(mailing)

    await bot.send_message(
        chat_id,
        f"Рассылка завершена\nСообщений отправлено - {mailing.sent_mailing_amount}/{len(all_custom_bot_users)}"
    )

    mailing.is_running = False
    mailing.sent_mailing_amount = 0

    await mailing_db.delete_mailing(mailing.mailing_id)
    # await asyncio.sleep(10) # For test only


@admin_bot_menu_router.callback_query(lambda query: InlinePostMessageMenuKeyboard.callback_validator(query.data))
async def mailing_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    callback_data = InlinePostMessageMenuKeyboard.Callback.model_validate_json(query.data)

    user_id = query.from_user.id
    mailing_id = callback_data.mailing_id
    bot_id = callback_data.bot_id

    try:
        mailing = await mailing_db.get_mailing(mailing_id)
    except MailingNotFound:
        logger.info(
            f"user_id={user_id}: tried to edit mailing_id={mailing_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_id=bot_id, mailing_id=mailing_id)
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
    ) and mailing.is_running:
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
                text=f"Отправлено {mailing.sent_mailing_amount}/{custom_users_length} сообщений",
                show_alert=True
            )
        case callback_data.ActionEnum.CANCEL:
            custom_users_length = len(await custom_bot_user_db.get_custom_bot_users(bot_id=bot_id))

            mailing.is_running = False

            try:
                await _scheduler.del_job_by_id(mailing.job_id)
            except Exception as e:
                logger.warning(
                    f"user_id={user_id}: Job ID {mailing.job_id} not found",
                    extra=extra_params(user_id=user_id, bot_id=bot_id, mailing_id=mailing_id),
                    exc_info=e
                )

            mailing.job_id = None

            await mailing_db.delete_mailing(mailing.mailing_id)

            await query.message.answer(
                f"Рассылка остановлена\nСообщений разослано - {mailing.sent_mailing_amount}/{custom_users_length}",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(bot_id),
                parse_mode=ParseMode.HTML
            )

        # NOT RUNNING ACTIONS
        case callback_data.ActionEnum.BUTTON_ADD:
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            if mailing.has_button:
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
                mailing.button_text = "Shop"
                mailing.button_url = f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id={bot_id}"
                mailing.has_button = True

                await mailing_db.update_mailing(mailing)

                await query.message.delete()
                await query.message.answer(
                    "Кнопка добавлена\n\n"
                    f"Сейчас там стандартный текст '{mailing.button_text}' и ссылка на Ваш магазин.\n"
                    "Эти два параметры Вы можете изменить в настройках рассылки"
                )
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
                )
        case callback_data.ActionEnum.BUTTON_URL:
            if not mailing.has_button:
                await _inline_no_button(query, bot_id, custom_bot_username)
            else:
                await query.message.answer(
                    "Введите ссылку, которая будет открываться у пользователей по нажатии на кнопку",
                    reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
                )
                await query.answer()
                await state.set_state(States.EDITING_MAILING_BUTTON_URL)
                await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})
        case callback_data.ActionEnum.BUTTON_TEXT:
            if not mailing.has_button:
                await _inline_no_button(query, bot_id, custom_bot_username)
            else:
                await query.message.answer(
                    "Введите текст, который будет отображаться на кнопке",
                    reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
                )
                await query.answer()
                await state.set_state(States.EDITING_MAILING_BUTTON_TEXT)
                await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})
        case callback_data.ActionEnum.BUTTON_DELETE:
            if not mailing.has_button:
                await _inline_no_button(query, bot_id, custom_bot_username)
            else:
                mailing.button_text = None
                mailing.button_url = None
                mailing.has_button = False

                await mailing_db.update_mailing(mailing)

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
            await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})
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
            await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})
        case callback_data.ActionEnum.START:
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            if await _is_post_message_valid(query, mailing, media_files):
                await query.message.edit_text(
                    text=MessageTexts.BOT_MAILINGS_MENU_ACCEPT_START.value.format(custom_bot_username),
                    reply_markup=InlinePostMessageStartConfirmKeyboard.get_keyboard(bot_id, mailing_id)
                )
        case callback_data.ActionEnum.DEMO:
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            if await _is_post_message_valid(query, mailing, media_files):
                await send_mailing_message(
                    bot,
                    query.from_user.id,
                    mailing,
                    media_files,
                    MailingMessageType.DEMO,
                    query.message
                )
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
                )
        case callback_data.ActionEnum.DELETE_POST_MESSAGE:
            await query.message.edit_text(
                text=MessageTexts.BOT_MAILINGS_MENU_ACCEPT_DELETING_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlinePostMessageAcceptDeletingKeyboard.get_keyboard(bot_id, mailing_id)
            )
        case callback_data.ActionEnum.EXTRA_SETTINGS:
            await query.message.edit_text(
                text=query.message.html_text + "\n\n🔎 Что такое <a href=\"https://www.google.com/url?sa=i&url=https%3A"
                                               "%2F%2Ftlgrm.ru%2Fblog%2Flink-preview.html&psig=AOvVaw27FhHb7fFrLDNGUX-u"
                                               "zG7y&ust=1717771529744000&source=images&cd=vfe&opi=89978449&ved=0CBIQjR"
                                               "xqFwoTCJj5puKbx4YDFQAAAAAdAAAAABAE\">предпросмотр ссылок</a>",
                reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
                    bot_id,
                    mailing_id,
                    mailing.enable_notification_sound,
                    mailing.enable_link_preview
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
            await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})

        case callback_data.ActionEnum.REMOVE_DELAY:
            mailing.is_delayed = False
            mailing.send_date = None

            await mailing_db.update_mailing(mailing)

            await query.message.edit_reply_markup(
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
            )


@admin_bot_menu_router.callback_query(
    lambda query: InlinePostMessageAcceptDeletingKeyboard.callback_validator(query.data)
)
async def mailing_accept_deleting_callback_handler(query: CallbackQuery):
    callback_data = InlinePostMessageAcceptDeletingKeyboard.Callback.model_validate_json(query.data)

    user_id = query.from_user.id
    mailing_id = callback_data.mailing_id
    bot_id = callback_data.bot_id

    try:
        mailing = await mailing_db.get_mailing(mailing_id)
    except MailingNotFound:
        logger.info(
            f"user_id={user_id}: tried to edit mailing_id={mailing_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_id=bot_id, mailing_id=mailing_id)
        )
        await query.answer("Рассылка уже завершена или удалена", show_alert=True)
        await query.message.delete()
        return

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    if callback_data.a != callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU and mailing.is_running:
        await query.answer("Рассылка уже запущена", show_alert=True)
        await query.message.edit_text(
            text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
            parse_mode=ParseMode.HTML
        )
        return

    match callback_data.a:
        case callback_data.ActionEnum.ACCEPT_DELETE:
            await mailing_db.delete_mailing(mailing_id)

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
    mailing_id = callback_data.mailing_id
    bot_id = callback_data.bot_id

    try:
        mailing = await mailing_db.get_mailing(mailing_id)
    except MailingNotFound:
        logger.info(
            f"user_id={user_id}: tried to edit mailing_id={mailing_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_id=bot_id, mailing_id=mailing_id)
        )
        await query.answer("Рассылка уже завершена или удалена", show_alert=True)
        await query.message.delete()
        return

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    if callback_data.a != callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU and mailing.is_running:
        await query.answer("Рассылка уже запущена", show_alert=True)
        await query.message.edit_text(
            text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
            parse_mode=ParseMode.HTML
        )
        return

    match callback_data.a:
        case callback_data.ActionEnum.LINK_PREVIEW:
            mailing.enable_link_preview = not mailing.enable_link_preview
            await mailing_db.update_mailing(mailing)

            await query.message.edit_reply_markup(
                reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
                    bot_id,
                    mailing_id,
                    mailing.enable_notification_sound,
                    mailing.enable_link_preview
                )
            )
        case callback_data.ActionEnum.NOTIFICATION_SOUND:
            mailing.enable_notification_sound = not mailing.enable_notification_sound
            await mailing_db.update_mailing(mailing)

            await query.message.edit_reply_markup(
                reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
                    bot_id,
                    mailing_id,
                    mailing.enable_notification_sound,
                    mailing.enable_link_preview
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
    mailing_id = callback_data.mailing_id
    bot_id = callback_data.bot_id

    try:
        mailing = await mailing_db.get_mailing(mailing_id)
    except MailingNotFound:
        logger.info(
            f"user_id={user_id}: tried to edit mailing_id={mailing_id} but it doesn't exist",
            extra=extra_params(user_id=user_id, bot_id=bot_id, mailing_id=mailing_id)
        )
        await query.answer("Рассылка уже завершена или удалена", show_alert=True)
        await query.message.delete()
        return

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    if callback_data.a != callback_data.ActionEnum.BACK_TO_POST_MESSAGE_MENU and mailing.is_running:
        await query.answer("Рассылка уже запущена", show_alert=True)
        await query.message.edit_text(
            text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(custom_bot_username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
            parse_mode=ParseMode.HTML
        )
        return

    match callback_data.a:
        case callback_data.ActionEnum.START_CONFIRM:
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            if await _is_post_message_valid(query, mailing, media_files):
                if mailing.is_delayed:
                    # Небольшой запас по времени
                    if datetime.now() > (mailing.send_date + timedelta(minutes=1)):
                        await query.answer(
                            text="Указанное время отправки уже прошло",
                            show_alert=True
                        )
                        return

                mailing.is_running = True

                if not mailing.is_delayed:
                    await mailing_db.update_mailing(mailing)
                    await send_mailing_messages(
                        custom_bot,
                        mailing,
                        media_files,
                        query.from_user.id
                    )
                else:
                    job_id = await _scheduler.add_scheduled_job(
                        func=send_mailing_messages, run_date=mailing.send_date,
                        args=[custom_bot, mailing, media_files, query.from_user.id])
                    mailing.job_id = job_id
                    await mailing_db.update_mailing(mailing)

                await query.message.answer(
                    f"Рассылка начнется в {mailing.send_date}" if mailing.is_delayed else "Рассылка началась"
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
    mailing_id = state_data["mailing_id"]

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    mailing = await mailing_db.get_mailing(mailing_id)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username)
        else:
            try:
                datetime_obj = datetime.strptime(message_text, "%d.%m.%Y %H:%M")
                datetime_obj.replace(tzinfo=None)

                if datetime.now() > datetime_obj:
                    return await message.reply("Введенное время уже прошло. Введите, пожалуйста, <b>будущее</b> время")

                mailing.is_delayed = True
                mailing.send_date = datetime_obj

                await mailing_db.update_mailing(mailing)

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
    mailing_id = state_data["mailing_id"]

    mailing = await mailing_db.get_mailing(mailing_id)
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username)
        else:
            mailing.description = message.html_text
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            await mailing_db.update_mailing(mailing)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            await send_mailing_message(
                bot,
                message.from_user.id,
                mailing,
                media_files,
                MailingMessageType.AFTER_REDACTING,
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
    mailing_id = state_data["mailing_id"]

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    mailing = await mailing_db.get_mailing(mailing_id)
    if not mailing.has_button:
        return await _reply_no_button(message, bot_id, custom_bot_username, state)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username)
        else:
            mailing.button_text = message.text
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)
            await mailing_db.update_mailing(mailing)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            await send_mailing_message(
                bot,
                message.from_user.id,
                mailing,
                media_files,
                MailingMessageType.AFTER_REDACTING,
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
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    mailing_id = state_data["mailing_id"]

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    mailing = await mailing_db.get_mailing(mailing_id)
    if not mailing.has_button:
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

            mailing.button_url = message.text
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)
            await mailing_db.update_mailing(mailing)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            await send_mailing_message(
                bot,
                message.from_user.id,
                mailing,
                media_files,
                MailingMessageType.AFTER_REDACTING,
                message
            )
            await message.answer(
                MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})
    else:
        await message.answer("Ссылка должна содержать только текст")


@admin_bot_menu_router.message(States.EDITING_MAILING_MEDIA_FILES)
async def editing_mailing_media_files_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    mailing_id = state_data["mailing_id"]

    if (message.photo or message.video or message.audio or message.document) and "first" not in state_data:
        await mailing_media_file_db.delete_mailing_media_files(mailing_id)
        state_data["first"] = True

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    match message.text:
        case ReplyConfirmMediaFilesKeyboard.Callback.ActionEnum.CONFIRM.value:
            return _back_to_post_message_menu(message, bot_id, custom_bot_username)
        case ReplyConfirmMediaFilesKeyboard.Callback.ActionEnum.CLEAR.value:
            await message.answer("Очищаем все файлы...")
            await mailing_media_file_db.delete_mailing_media_files(mailing_id=mailing_id)
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

    await mailing_media_file_db.add_mailing_media_file(MailingMediaFileSchema.model_validate(
        {"mailing_id": mailing_id, "file_id_main_bot": file_id,
         "file_path": file_path, "media_type": media_type}
    ))

    await message.answer(answer_text)


async def send_mailing_message(  # TODO that's not funny
        bot_from_send: Bot,
        to_user_id: int,
        mailing_schema: MailingSchema,
        media_files: list[MailingMediaFileSchema],
        mailing_message_type: MailingMessageType,
        message: Message = None,
) -> None:
    if mailing_schema.has_button:
        if mailing_schema.button_url == f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id={mailing_schema.bot_id}":
            button = InlineKeyboardButton(
                text=mailing_schema.button_text,
                web_app=make_webapp_info(bot_id=mailing_schema.bot_id)
            )
        else:
            button = InlineKeyboardButton(
                text=mailing_schema.button_text,
                url=mailing_schema.button_url
            )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [button]
            ]
        )
    else:
        keyboard = None

    if len(media_files) >= 1:
        is_first_message = False
        media_group = []
        for media_file in media_files:
            if mailing_message_type == MailingMessageType.RELEASE:
                # мда, ну короче на серверах фотки хранятся только у главного бота, т.к через него админ создавал
                # рассылки. В кастомных ботах нет того file_id, который есть в главном боте, поэтому, если у нас
                # file_id_custom_bot == None, значит это первое сообщение из всей рассылки. Поэтому мы скачиваем файл
                # с серверов главного бота и отправляем это в кастомном, чтобы получить file_id для кастомного и
                # сохраняем в бд.
                # При следующей отправки тут уже не будет None
                if media_file.file_id_custom_bot is None:
                    is_first_message = True
                    file_path = media_file.file_path
                    file_bytes = await bot.download_file(
                        file_path=file_path,
                    )
                    file_name = BufferedInputFile(
                        file=file_bytes.read(),
                        filename=file_path
                    )
                else:
                    file_name = media_file.file_id_custom_bot
            else:
                file_name = media_file.file_id_main_bot
            if media_file.media_type == "photo":
                media_group.append(InputMediaPhoto(media=file_name) if len(
                    media_files) > 1 else file_name)
            elif media_file.media_type == "video":
                media_group.append(InputMediaVideo(media=file_name) if len(
                    media_files) > 1 else file_name)
            elif media_file.media_type == "audio":
                media_group.append(InputMediaAudio(media=file_name) if len(
                    media_files) > 1 else file_name)
            elif media_file.media_type == "document":
                media_group.append(InputMediaDocument(
                    media=file_name) if len(media_files) > 1 else file_name)

        uploaded_media_files = []
        if len(media_files) > 1:
            if mailing_schema.description:
                media_group[0].caption = mailing_schema.description

            uploaded_media_files.extend(await bot_from_send.send_media_group(
                chat_id=to_user_id,
                media=media_group,
                disable_notification=not mailing_schema.enable_link_preview,
            ))
            if message:
                await message.delete()
        elif len(media_files) == 1:
            media_file = media_files[0]

            if media_file.media_type == "photo":
                method = bot_from_send.send_photo
            elif media_file.media_type == "video":
                method = bot_from_send.send_video
            elif media_file.media_type == "audio":
                method = bot_from_send.send_audio
            elif media_file.media_type == "document":
                method = bot_from_send.send_document
            else:
                raise Exception("Unexpected type")

            uploaded_media_files.append(await method(
                to_user_id,
                media_group[0],
                caption=mailing_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    mailing_schema.enable_notification_sound),
            ))

            if message:
                await message.delete()

        if is_first_message:  # первое сообщение, отправленное в рассылке с кастомного бота. Сохраняем file_id в бд
            for ind in range(len(uploaded_media_files)):
                new_message = uploaded_media_files[ind]
                old_message = media_files[ind]
                if new_message.photo:
                    file_id = new_message.photo[-1].file_id
                elif new_message.video:
                    file_id = new_message.video.file_id
                elif new_message.audio:
                    file_id = new_message.audio.file_id
                elif new_message.document:
                    file_id = new_message.document.file_id
                else:
                    raise Exception("unsupported type")

                old_message.file_id_custom_bot = file_id
                await mailing_media_file_db.update_media_file(old_message)
    else:
        if mailing_schema.description is None:
            return
        if mailing_message_type == MailingMessageType.DEMO:  # только при демо с главного бота срабатывает
            await message.edit_text(
                text=mailing_schema.description,
                link_preview_options=LinkPreviewOptions(is_disabled=not (
                    mailing_schema.enable_link_preview)),
                reply_markup=keyboard,
            )
        elif mailing_message_type == MailingMessageType.AFTER_REDACTING:
            await bot_from_send.send_message(
                chat_id=to_user_id,
                text=mailing_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    mailing_schema.enable_notification_sound),
                link_preview_options=LinkPreviewOptions(is_disabled=not (
                    mailing_schema.enable_link_preview))
            )
        else:
            await bot_from_send.send_message(
                chat_id=to_user_id,
                text=mailing_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    mailing_schema.enable_notification_sound),
                link_preview_options=LinkPreviewOptions(is_disabled=not (
                    mailing_schema.enable_link_preview))
            )


async def _inline_no_button(query: CallbackQuery, bot_id: int, custom_bot_username: str) -> None:
    await query.answer(
        "В этом рассылочном сообщении кнопки нет", show_alert=True
    )
    await query.message.edit_text(
        text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
        parse_mode=ParseMode.HTML
    )


async def _reply_no_button(message: Message, bot_id: int, custom_bot_username: str, state: FSMContext) -> None:
    await message.answer(
        "В рассылочном сообщении кнопки уже нет",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
    )
    await message.answer(
        MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
    )

    await state.set_state(States.BOT_MENU)
    await state.set_data({"bot_id": bot_id})


async def _inline_back_to_post_message_menu(query: CallbackQuery, bot_id: int, custom_bot_username: str) -> None:
    await query.message.edit_text(
        text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id),
        parse_mode=ParseMode.HTML
    )


async def _back_to_post_message_menu(message: Message, bot_id: int, custom_bot_username: str) -> None:
    await message.answer(
        "Возвращаемся в меню...",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
    )
    await message.answer(
        text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
            custom_bot_username
        ),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id)
    )


async def _is_post_message_valid(
        query: CallbackQuery,
        mailing: MailingSchema,
        media_files: list[MailingMediaFileSchema]
) -> bool:
    if len(media_files) > 1 and mailing.has_button:
        await query.answer(
            "Telegram не позволяет прикрепить кнопку, если в сообщении минимум 2 медиафайла",
            show_alert=True
        )
        return False
    elif not media_files and not mailing.description:
        await query.answer(
            text="В Вашем рассылочном сообщении нет ни текста, ни медиафайлов",
            show_alert=True
        )
        return False

    return True
