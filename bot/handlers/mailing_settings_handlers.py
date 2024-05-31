import asyncio
import json
import os
import string
from io import BytesIO
from random import sample
from datetime import datetime
from typing import Dict, Any

from aiogram.fsm.storage.base import StorageKey
from aiohttp import ClientConnectorError

from aiogram import Bot, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest
from aiogram.utils.token import validate_token, TokenValidationError

from aiogram.types import Message, FSInputFile, CallbackQuery, ReplyKeyboardRemove, MessageEntity, LinkPreviewOptions, \
    InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument, InputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext

from bot.main import bot, user_db, bot_db, product_db, order_db, custom_bot_user_db, QUESTION_MESSAGES, competition, \
    mailing_media_file_db
from bot.config import logger
from bot.keyboards import *
from bot.exceptions import InstanceAlreadyExists
from bot.states.states import States
from bot.handlers.routers import admin_bot_menu_router
from bot.utils.custom_bot_api import start_custom_bot, stop_custom_bot

from custom_bots.multibot import storage as custom_bot_storage

from database.models.bot_model import BotSchemaWithoutId
from database.models.mailing_media_files import MailingMediaFileSchema
from database.models.order_model import OrderSchema, OrderNotFound
from database.models.product_model import ProductWithoutId


class MailingMessageType(Enum):
    DEMO = "demo"  # Демо сообщение с главного бота
    AFTER_REDACTING = "after_redacting"  # Демо сообщение с главного бота (но немного другой функионал для отправки)
    RELEASE = "release"  # Главная рассылка (отправка с кастомного бота всем пользователям)


@admin_bot_menu_router.callback_query(lambda query: query.data.startswith("mailing_menu"))
async def mailing_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    query_data = query.data.split(":")

    action = query_data[1]
    bot_id = int(query_data[2])
    mailing_id = int(query_data[3])

    mailing = await mailing_db.get_mailing(mailing_id)
    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

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
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
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
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
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
                                       reply_markup=get_back_keyboard("✅ Готово"))
            await query.answer()
            await state.set_state(States.EDITING_MAILING_MEDIA_FILES)
            await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})
        case "start":
            all_custom_bot_users = await custom_bot_user_db.get_custom_bot_users(custom_bot.bot_id)
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            custom_bot_tg = Bot(custom_bot.token, parse_mode=ParseMode.HTML)
            for ind, user in enumerate(all_custom_bot_users, start=1):
                await send_mailing_message(
                    bot_from_send=custom_bot_tg,
                    to_user_id=user.user_id,
                    mailing_schema=mailing,
                    media_files=media_files,
                    mailing_message_type=MailingMessageType.RELEASE,
                    message=None,
                )
                logger.info(f"mailing with mailing_id {mailing_id} has sent to {ind}/{len(all_custom_bot_users)} with user_id {user.user_id}")
                await asyncio.sleep(.05)  # 20 messages per second (limit is 30)
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
                    MailingMessageType.AFTER_REDACTING,
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
                text=MessageTexts.BOT_MAILINGS_MENU_ACCEPT_DELETING_MESSAGE.value.format(custom_bot_username),
                reply_markup=await get_inline_bot_mailing_menu_accept_deleting_keyboard(bot_id, mailing_id)
            )
        case "accept_delete":
            await mailing_db.delete_mailing(mailing_id)
            await query.message.answer(
                "Рассылочное сообщение удалено",
                reply_markup=get_reply_bot_menu_keyboard(bot_id)
            )
            await query.message.edit_text(
                text=MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=await get_inline_bot_menu_keyboard(bot_id)
            )


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
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
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
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
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
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
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
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
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
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
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
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
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
            reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
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
            reply_markup=get_back_keyboard("✅ Готово")
        )

    await mailing_media_file_db.add_mailing_media_file(MailingMediaFileSchema.model_validate(
        {"mailing_id": mailing_id, "file_id_main_bot": file_id, "file_path": file_path, "media_type": media_type}
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
        button = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=mailing_schema.button_text, url=mailing_schema.button_url)]
            ]
        )
    else:
        button = None

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
                media_group.append(InputMediaPhoto(media=file_name) if len(media_files) > 1 else file_name)
            elif media_file.media_type == "video":
                media_group.append(InputMediaVideo(media=file_name) if len(media_files) > 1 else file_name)
            elif media_file.media_type == "audio":
                media_group.append(InputMediaAudio(media=file_name) if len(media_files) > 1 else file_name)
            elif media_file.media_type == "document":
                media_group.append(InputMediaDocument(media=file_name) if len(media_files) > 1 else file_name)

        uploaded_media_files = []
        if len(media_files) > 1:
            if mailing_schema.description:
                media_group[0].caption = mailing_schema.description

            uploaded_media_files.extend(await bot_from_send.send_media_group(
                chat_id=to_user_id,
                media=media_group
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
                reply_markup=button
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
                link_preview_options=LinkPreviewOptions(is_disabled=True),
                reply_markup=button,
            )
        else:
            await bot_from_send.send_message(
                chat_id=to_user_id,
                text=mailing_schema.description,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
                reply_markup=button
            )
