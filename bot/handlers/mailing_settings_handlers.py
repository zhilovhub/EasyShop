import json
import os
import string
from random import sample
from datetime import datetime
from typing import Dict, Any

from aiogram.fsm.storage.base import StorageKey
from aiohttp import ClientConnectorError

from aiogram import Bot, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.utils.token import validate_token, TokenValidationError

from aiogram.types import Message, FSInputFile, CallbackQuery, ReplyKeyboardRemove, MessageEntity, LinkPreviewOptions, \
    InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument, InputFile
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
            pass
        case "demo":
            media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

            if len(media_files) > 1 and mailing.has_button:
                await query.answer(
                    "Telegram не позволяет прикрепить кнопку, если в сообщении минимум 2 медиафайла",
                    show_alert=True
                )
            elif mailing.description or media_files:
                await send_demonstration(
                    mailing,
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
            await mailing_db.update_mailing(mailing)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await send_demonstration(
                mailing,
                message,
                is_demo=False
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
            await mailing_db.update_mailing(mailing)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await send_demonstration(
                mailing,
                message,
                is_demo=False
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
            await mailing_db.update_mailing(mailing)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await send_demonstration(
                mailing,
                message,
                is_demo=False
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
    elif message.photo:
        photo = message.photo[-1]
        await mailing_media_file_db.add_mailing_media_file(MailingMediaFileSchema.model_validate(
            {"mailing_id": mailing_id, "file_name": photo.file_id, "media_type": "photo"}
        ))

        await message.answer(
            f"Фото {photo.file_unique_id} добавлено"
        )
    elif message.video:
        video = message.video
        await mailing_media_file_db.add_mailing_media_file(MailingMediaFileSchema.model_validate(
            {"mailing_id": mailing_id, "file_name": video.file_id, "media_type": "video"}
        ))

        await message.answer(
            f"Видео {video.file_name} добавлено"
        )
    elif message.audio:
        audio = message.audio
        await mailing_media_file_db.add_mailing_media_file(MailingMediaFileSchema.model_validate(
            {"mailing_id": mailing_id, "file_name": audio.file_id, "media_type": "audio"}
        ))

        await message.answer(
            f"Аудио {audio.file_name} добавлено"
        )
    elif message.document:
        document = message.document
        await mailing_media_file_db.add_mailing_media_file(MailingMediaFileSchema.model_validate(
            {"mailing_id": mailing_id, "file_name": document.file_id, "media_type": "document"}
        ))

        await message.answer(
            f"Документ {document.file_name} добавлен"
        )

    else:
        await message.answer(
            "Пришлите медиафайлы (фото, видео, аудио, документы), которые должны быть прикреплены к рассылочному сообщению",
            reply_markup=get_back_keyboard("✅ Готово")
        )


async def send_demonstration(
        mailing_schema: MailingSchema,
        message: Message,
        is_demo: bool = True
) -> None:
    mailing_id = mailing_schema.mailing_id
    media_files = await mailing_media_file_db.get_all_mailing_media_files(mailing_id)

    if mailing_schema.has_button:
        button = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=mailing_schema.button_text, url=mailing_schema.button_url)]
            ]
        )
    else:
        button = None

    if len(media_files) > 1:
        media_group = []
        for media_file in media_files:
            if media_file.media_type == "photo":
                media_group.append(InputMediaPhoto(media=media_file.file_name))
            elif media_file.media_type == "video":
                media_group.append(InputMediaVideo(media=media_file.file_name))
            elif media_file.media_type == "audio":
                media_group.append(InputMediaAudio(media=media_file.file_name))
            elif media_file.media_type == "document":
                media_group.append(InputMediaDocument(media=media_file.file_name))

        if mailing_schema.description:
            media_group[0].caption = mailing_schema.description

        await bot.send_media_group(
            chat_id=message.chat.id,
            media=media_group
        )
        await message.delete()
    elif len(media_files) == 1:
        media_file = media_files[0]
        if media_file.media_type == "photo":
            method = bot.send_photo
        elif media_file.media_type == "video":
            method = bot.send_video
        elif media_file.media_type == "audio":
            method = bot.send_audio
        elif media_file.media_type == "document":
            method = bot.send_document
        else:
            raise Exception("Unexpected type")

        await method(
            message.chat.id,
            media_file.file_name,
            caption=mailing_schema.description,
            reply_markup=button
        )
        await message.delete()
    else:
        if is_demo:
            await message.edit_text(
                text=mailing_schema.description,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
                reply_markup=button,
            )
        else:
            await message.answer(
                text=mailing_schema.description,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
                reply_markup=button
            )
