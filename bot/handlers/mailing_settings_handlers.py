import asyncio
from datetime import datetime, timedelta

from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.types import Message, CallbackQuery, LinkPreviewOptions, \
    InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument, BufferedInputFile
from aiogram.fsm.context import FSMContext

from bot.main import bot, custom_bot_user_db, mailing_media_file_db, _scheduler
from bot.keyboards import *
from bot.states.states import States
from bot.handlers.routers import admin_bot_menu_router

from database.models.mailing_media_files import MailingMediaFileSchema

from logs.config import logger


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

        if mailing.is_running == False:
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
            f"mailing with mailing_id {mailing_id} has sent to {ind}/{len(all_custom_bot_users)} with user_id {user.user_id}")
        # 20 messages per second (limit is 30)
        await asyncio.sleep(.05)
        mailing.sent_mailing_amount += 1
        await mailing_db.update_mailing(mailing)

    await bot.send_message(chat_id, f"Рассылка завершена\nСообщений отправлено - {mailing.sent_mailing_amount}/{len(all_custom_bot_users)}")

    mailing.is_running = False
    mailing.sent_mailing_amount = 0

    await mailing_db.delete_mailing(mailing.mailing_id)
    # await asyncio.sleep(10) # For test only


@admin_bot_menu_router.callback_query(lambda query: query.data.startswith("mailing_menu"))
async def mailing_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    query_data = query.data.split(":")

    action = query_data[1]
    bot_id = int(query_data[2])
    mailing_id = int(query_data[3])
    try:
        mailing = await mailing_db.get_mailing(mailing_id)
    except MailingNotFound:
        await query.answer("Рассылка уже удалена", show_alert=True)
        await query.message.delete()
        return
    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username
    if mailing.is_running == True:
        match action:
            case "check_mailing_stats":
                custom_users_length = len(await custom_bot_user_db.get_custom_bot_users(bot_id=bot_id))

                await query.answer(
                    text=f"Отправлено {mailing.sent_mailing_amount}/{custom_users_length} сообщений",
                    show_alert=True
                )
            case "stop_mailing":
                custom_users_length = len(await custom_bot_user_db.get_custom_bot_users(bot_id=bot_id))

                mailing.is_running = False
                mailing.sent_mailing_amount = 0
                try:
                    await _scheduler.del_job_by_id(mailing.job_id)
                except:
                    logger.warning(f"Job ID {mailing.job_id} not found")
                mailing.job_id = None

                await mailing_db.delete_mailing(mailing.mailing_id)

                await query.message.answer(f"Рассылка остановлена\nСообщений разослано - {mailing.sent_mailing_amount}/{custom_users_length}")

                await query.message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await get_inline_bot_menu_keyboard(bot_id)
                )
                await query.message.delete()
            case _:
                await query.answer("Рассылка уже запущена", show_alert=True)
                return await query.message.delete()

    match action:
        case "button_url":
            if not mailing.has_button:
                await query.answer("В рассылочном сообщении кнопки уже нет", show_alert=True)
                await query.message.delete()
            else:
                await query.message.answer("Введите ссылку, которая будет открываться по нажатию на кнопку",
                                           reply_markup=get_back_keyboard())
                await query.answer()
                await state.set_state(States.EDITING_MAILING_BUTTON_URL)
                await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})
        case "button_text":
            if not mailing.has_button:
                await query.answer("В рассылочном сообщении кнопки уже нет", show_alert=True)
                await query.message.delete()
            else:
                await query.message.answer("Введите текст, который будет отображаться на кнопке",
                                           reply_markup=get_back_keyboard())
                await query.answer()
                await state.set_state(States.EDITING_MAILING_BUTTON_TEXT)
                await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})
        case "delete_button":
            if not mailing.has_button:
                await query.answer("В рассылочном сообщении кнопки уже нет", show_alert=True)
                await query.message.delete()
            else:
                mailing.button_text = None
                mailing.button_url = None
                mailing.has_button = False
                await mailing_db.update_mailing(mailing)

                await query.message.answer("Кнопка удалена\n\n")
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                        custom_bot_username),
                    reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
                )
        case "add_button":
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            if mailing.has_button:
                await query.answer("В рассылочном сообщении кнопка уже есть", show_alert=True)
                await query.message.delete()
            elif len(media_files) > 1:
                await query.answer("Кнопку нельзя добавить, если в сообщение больше одного медиафайла", show_alert=True)
            else:
                mailing.button_text = "Shop"
                mailing.button_url = f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id={bot_id}"
                mailing.has_button = True
                await mailing_db.update_mailing(mailing)

                await query.message.answer("Кнопка добавлена\n\n"
                                           "Сейчас там стандартный текст 'Магазин' и ссылка на Ваш магазин.\n"
                                           "Эти два параметры Вы можете изменить в настройках рассылки")
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                        custom_bot_username),
                    reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
                )

        case "message":
            await query.message.answer("Введите текст, который будет отображаться в рассылочном сообщении",
                                       reply_markup=get_back_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_MAILING_MESSAGE)
            await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})
        case "media":
            await query.message.answer("Отправьте одним сообщение медиафайлы для рассылочного сообщения\n\n"
                                       "❗ Старые медиафайлы к этому рассылочному сообщению <b>перезапишутся</b>\n\n"
                                       "❗❗ Обратите внимание, что к сообщению нельзя будет прикрепить кнопку, если медиафайлов <b>больше одного</b>",
                                       reply_markup=get_confirm_media_upload_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_MAILING_MEDIA_FILES)
            await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})
        case "start":
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            if len(media_files) > 1 and mailing.has_button:
                return await query.answer(
                    "Telegram не позволяет прикрепить кнопку, если в сообщении минимум 2 медиафайла",
                    show_alert=True
                )
            elif not media_files and not mailing.description:
                return await query.answer(
                    text="В Вашем рассылочном сообщении нет ни текста, ни медиафайлов",
                    show_alert=True
                )

            await query.message.edit_text(
                text=MessageTexts.BOT_MAILINGS_MENU_ACCEPT_START.value.format(
                    custom_bot_username),
                reply_markup=await get_inline_bot_mailing_start_confirm_keybaord(bot_id, mailing_id)
            )
        case "demo":
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            if len(media_files) > 1 and mailing.has_button:
                await query.answer(
                    "Telegram не позволяет прикрепить кнопку, если в сообщении минимум 2 медиафайла",
                    show_alert=True
                )
            elif mailing.description or media_files:
                media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)
                await send_mailing_message(
                    bot,
                    query.from_user.id,
                    mailing,
                    media_files,
                    MailingMessageType.DEMO,
                    query.message
                )
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                        custom_bot_username
                    ),
                    reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
                )

            else:
                await query.answer(
                    text="В Вашем рассылочном сообщении нет ни текста, ни медиафайлов",
                    show_alert=True
                )
        case "delete_mailing":
            await query.message.edit_text(
                text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(
                    custom_bot_username),
                reply_markup=await get_inline_bot_mailing_menu_accept_deleting_keyboard(bot_id, mailing_id)
            )
        case "accept_delete":
            await mailing_db.delete_mailing(mailing_id)
            await query.answer(
                text="Рассылочное сообщение удалено",
                show_alert=True
            )
            await query.message.answer(
                text=MessageTexts.BOT_MENU_MESSAGE.value.format(
                    custom_bot_username),
                reply_markup=await get_inline_bot_menu_keyboard(
                    bot_id)
            )
            await query.message.delete()
            # await new_message.edit_reply_markup(reply_markup=await get_inline_bot_menu_keyboard(
            #     bot_id))
        case "accept_start":
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            if len(media_files) > 1 and mailing.has_button:
                await query.answer(
                    "Telegram не позволяет прикрепить кнопку, если в сообщении минимум 2 медиафайла",
                    show_alert=True
                )

            elif mailing.description or media_files:
                if mailing.is_delayed:
                    # Небольшой запас по времени
                    if datetime.now() > (mailing.send_date + timedelta(minutes=2)):
                        await query.answer(
                            text="Указанное время отправки уже прошло",
                            show_alert=True
                        )
                        return
                mailing.is_running = True
                await mailing_db.update_mailing(mailing)

                text = f"Рассылка начнется в {mailing.send_date}" if mailing.is_delayed else "Рассылка началась"
                await query.message.answer(text)

                await query.message.edit_text(
                    text=MessageTexts.BOT_MAILING_MENU_WHILE_RUNNING.value.format(
                        custom_bot_username),
                    reply_markup=await get_inline_bot_mailing_menu_keyboard(
                        bot_id)
                )

                if not (mailing.is_delayed):
                    await send_mailing_messages(
                        custom_bot,
                        mailing,
                        media_files,
                        query.from_user.id
                    )
                else:
                    job_id = await _scheduler.add_scheduled_job(
                        func=send_mailing_messages, run_date=mailing.send_date, args=[custom_bot, mailing, media_files, query.from_user.id])
                    mailing.job_id = job_id
                    await mailing_db.update_mailing(mailing)
            else:
                await query.answer(
                    text="В Вашем рассылочном сообщении нет ни текста, ни медиафайлов",
                    show_alert=True
                )

        case "extra_settings":
            await query.message.edit_reply_markup(
                text=query.message.text + "\n\n🔎 Что такое <a href=\"https://www.google.com/url?sa=i&url=https%3A%2F%2Ftlgrm.ru%2Fblog%2Flink-preview.html&psig=AOvVaw27FhHb7fFrLDNGUX-uzG7y&ust=1717771529744000&source=images&cd=vfe&opi=89978449&ved=0CBIQjRxqFwoTCJj5puKbx4YDFQAAAAAdAAAAABAE\">предпросмотр ссылок</a>",
                reply_markup=await get_inline_bot_mailing_menu_extra_settings_keyboard(
                    bot_id,
                    mailing_id,
                    mailing.enable_notification_sound,
                    mailing.enable_link_preview
                )
            )
        case "toggle_link_preview":
            mailing.enable_link_preview = False if mailing.enable_link_preview else True
            await mailing_db.update_mailing(mailing)
            await query.message.edit_reply_markup(
                reply_markup=await get_inline_bot_mailing_menu_extra_settings_keyboard(
                    bot_id,
                    mailing_id,
                    mailing.enable_notification_sound,
                    mailing.enable_link_preview
                )
            )
        case "toggle_notigication_sound":
            mailing.enable_notification_sound = False if mailing.enable_notification_sound else True
            await mailing_db.update_mailing(mailing)
            await query.message.edit_reply_markup(
                reply_markup=await get_inline_bot_mailing_menu_extra_settings_keyboard(
                    bot_id,
                    mailing_id,
                    mailing.enable_notification_sound,
                    mailing.enable_link_preview
                )
            )
        case "delay":
            await query.message.answer(f"Введите дату рассылки\n\n{MessageTexts.DATE_RULES.value}",
                                       reply_markup=get_back_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_DELAY_DATE)
            await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})

        case "cancel_delay":
            mailing.is_delayed = False
            mailing.send_date = None
            await mailing_db.update_mailing(mailing)
            await query.message.edit_reply_markup(reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id))


@admin_bot_menu_router.message(States.EDITING_DELAY_DATE)
async def editing_mailing_delay_date_handler(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    mailing_id = state_data["mailing_id"]

    mailing = await mailing_db.get_mailing(mailing_id)
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            await message.answer(
                text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                    custom_bot_username
                ),
                reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
            )
        else:
            try:
                datetime_obj = datetime.strptime(
                    message_text, "%d.%m.%Y %H:%M")
                datetime_obj.replace(tzinfo=None)
                if datetime.now() > datetime_obj:
                    await message.reply("Введенное время уже прошло, попробуйте ввести другое")
                    return
                mailing.is_delayed = True
                mailing.send_date = datetime_obj

                await mailing_db.update_mailing(mailing)

                await message.reply(f"Запланировано на: {datetime_obj.strftime('%Y-%m-%d %H:%M')}\n\n"
                                    f"Для запуска отложенной рассылки нажмите <b>Запустить</b>")
                await message.answer(
                    MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                        custom_bot_username
                    ),
                    reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
                )

                await state.set_state(States.BOT_MENU)
                await state.set_data({"bot_id": bot_id})
            except ValueError:
                await message.reply("Некорректный формат. Пожалуйста, введите время и дату в правильном формате.")


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
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            await message.answer(
                text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                    custom_bot_username
                ),
                reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
            )
        else:
            mailing.description = message.html_text
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            await mailing_db.update_mailing(mailing)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
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
                MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                    custom_bot_username
                ),
                reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})
    else:
        await message.answer("Описание должно содержать текст.\n"
                             "Если есть необходимость прикрепить медиафайлы, то для этого есть пункт в меню")


@admin_bot_menu_router.message(States.EDITING_MAILING_BUTTON_TEXT)
async def editing_mailing_button_text_handler(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    mailing_id = state_data["mailing_id"]

    mailing = await mailing_db.get_mailing(mailing_id)
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            await message.answer(
                text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                    custom_bot_username
                ),
                reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
            )
        else:
            mailing.button_text = message.text
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)
            await mailing_db.update_mailing(mailing)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
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
                MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                    custom_bot_username
                ),
                reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
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

    mailing = await mailing_db.get_mailing(mailing_id)
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            await message.answer(
                text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                    custom_bot_username
                ),
                reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
            )
        else:
            mailing.button_url = message.text
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)
            await mailing_db.update_mailing(mailing)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
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
                MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                    custom_bot_username
                ),
                reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})
    else:
        await message.answer("Ссылка должно содержать только текст")


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

    if message.text == "✅ Готово":
        await message.answer(
            "Возвращаемся в меню...",
            reply_markup=get_reply_bot_menu_keyboard(
                bot_id=state_data["bot_id"])
        )
        await message.answer(
            text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                custom_bot_username
            ),
            reply_markup=await get_inline_bot_mailing_menu_keyboard(bot_id)
        )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})

        return
    elif message.text == "Очистить":
        await message.answer("Очищаем все файлы...")
        await mailing_media_file_db.delete_mailing_media_files(mailing_id=mailing_id)
        await message.answer("Отправьте одним сообщение медиафайлы для рассылочного сообщения\n\n"
                             "❗ Старые медиафайлы к этому рассылочному сообщению <b>перезапишутся</b>\n\n"
                             "❗❗ Обратите внимание, что к сообщению нельзя будет прикрепить кнопку, если медиафайлов <b>больше одного</b>",
                             reply_markup=get_confirm_media_upload_keyboard())
        return
    elif message.photo:
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
            "Пришлите медиафайлы (фото, видео, аудио, документы), которые должны быть прикреплены к рассылочному сообщению",
            reply_markup=get_confirm_media_upload_keyboard()
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
                if media_file.file_id_custom_bot == None:
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
                disable_notification=not (mailing_schema.enable_link_preview),
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
