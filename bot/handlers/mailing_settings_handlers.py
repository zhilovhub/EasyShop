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
    InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument
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
            if mailing.has_button:
                await query.answer("В рассылочном сообщении кнопка уже есть", show_alert=True)
                await query.message.delete()
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
                                       "❗ Старые медиафайлы к этому рассылочному сообщению <b>перезапишутся</b>",
                                       reply_markup=get_back_keyboard("✅ Готово"))
            await query.answer()
            await state.set_state(States.EDITING_MAILING_MEDIA_FILES)
            await state.set_data({"bot_id": bot_id, "mailing_id": mailing_id})
        case "start":
            pass
        case "demo":
            pass
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
            # await send_demonstration(  # TODO сделать
            #     competition_schema,
            #     message,
            #     is_demo=False
            # )
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
            # await send_demonstration(  # TODO сделать
            #     competition_schema,
            #     message,
            #     is_demo=False
            # )
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
            # await send_demonstration(  # TODO сделать
            #     competition_schema,
            #     message,
            #     is_demo=False
            # )
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
        await message.answer("Пришлите медиафайлы (фото, видео, аудио, документы), которые должны быть прикреплены к рассылочному сообщению")
