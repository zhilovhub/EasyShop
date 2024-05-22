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

from bot.main import bot, user_db, bot_db, product_db, order_db, custom_bot_user_db, QUESTION_MESSAGES, competition
from bot.config import logger
from bot.keyboards import *
from bot.exceptions import InstanceAlreadyExists
from bot.states.states import States
from bot.handlers.routers import admin_bot_menu_router
from bot.utils.custom_bot_api import start_custom_bot, stop_custom_bot

from custom_bots.multibot import storage as custom_bot_storage

from database.models.bot_model import BotSchemaWithoutId
from database.models.order_model import OrderSchema, OrderNotFound
from database.models.product_model import ProductWithoutId


@admin_bot_menu_router.callback_query(lambda query: query.data.startswith("mailing_menu"))
async def mailing_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    query_data = query.data.split(":")

    action = query_data[1]
    bot_id = int(query_data[2])
    mailing_id = int(query_data[3])

    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_username = (await Bot(custom_bot.token).get_me()).username

    match action:
        case "button_url":
            pass
        case "button_text":
            pass
        case "delete_button":
            pass
        case "add_button":
            pass
        case "text":
            pass
        case "media":
            pass
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


@admin_bot_menu_router.message(States.EDITING_COMPETITION_NAME)
async def editing_competition_name_handler(message: Message, state: FSMContext):
    message_text = message.text

    state_data = await state.get_data()

    competition_id = state_data["competition_id"]
    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]

    competition_schema = await competition.get_competition(competition_id)
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username
    channel_username = (await custom_bot_tg.get_chat(channel_id)).username

    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                text=MessageTexts.BOT_COMPETITION_MENU_MESSAGE.value.format(
                    competition_schema.name,
                    channel_username,
                    custom_bot_username
                ),
                reply_markup=await get_competition_menu_keyboard(competition_id)
            )
        else:
            competition_schema.name = message_text
            await competition.update_competition(competition_schema)

            await message.answer(
                MessageTexts.BOT_COMPETITION_MENU_MESSAGE.value.format(
                    competition_schema.name,
                    channel_username,
                    custom_bot_username
                ),
                reply_markup=await get_competition_menu_keyboard(competition_id)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})
    else:
        await message.answer("Короткое название отображается только у Вас для удобной ориентации по созданным конкурсам\n"
                             "Оно должно являться <b>текстом</b>, максимальная длина которого <b>40 символов</b>")


@admin_bot_menu_router.message(States.EDITING_COMPETITION_DESCRIPTION)
async def editing_competition_description_handler(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()

    competition_id = state_data["competition_id"]
    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]

    competition_schema = await competition.get_competition(competition_id)
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username
    channel_username = (await custom_bot_tg.get_chat(channel_id)).username

    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                text=MessageTexts.BOT_COMPETITION_MENU_MESSAGE.value.format(
                    competition_schema.name,
                    channel_username,
                    custom_bot_username
                ),
                reply_markup=await get_competition_menu_keyboard(competition_id)
            )
        else:
            competition_schema.description = message.html_text
            await competition.update_competition(competition_schema)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
            )
            await send_demonstration(
                competition_schema,
                message,
                is_demo=False
            )
            await message.answer(
                MessageTexts.BOT_COMPETITION_MENU_MESSAGE.value.format(
                    competition_schema.name,
                    channel_username,
                    custom_bot_username
                ),
                reply_markup=await get_competition_menu_keyboard(competition_id)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})
    else:
        await message.answer("Описание должно содержать текст.\n"
                             "Если есть необходимость прикрепить медиафайлы, то для этого есть пункт в меню")


@admin_bot_menu_router.message(States.EDITING_COMPETITION_MEDIA_FILES)
async def editing_competition_media_files_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    competition_id = state_data["competition_id"]
    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]

    if (message.photo or message.video or message.audio or message.document) and "first" not in state_data:
        await competition.delete_competition_media_files(competition_id)
        state_data["first"] = True

    competition_schema = await competition.get_competition(competition_id)
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username
    channel_username = (await custom_bot_tg.get_chat(channel_id)).username

    if message.text == "✅ Готово":
        await message.answer(
            "Возвращаемся в меню...",
            reply_markup=get_reply_bot_menu_keyboard(bot_id=state_data["bot_id"])
        )
        await message.answer(
            text=MessageTexts.BOT_COMPETITION_MENU_MESSAGE.value.format(
                competition_schema.name,
                channel_username,
                custom_bot_username
            ),
            reply_markup=await get_competition_menu_keyboard(competition_id)
        )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id})
    elif message.photo:
        photo = message.photo[-1]
        await competition.add_competition_media_file(competition_id, photo.file_id, "photo")

        await message.answer(
            f"Фото {photo.file_unique_id} добавлено"
        )
    elif message.video:
        video = message.video
        await competition.add_competition_media_file(competition_id, video.file_id, "video")

        await message.answer(
            f"Видео {video.file_name} добавлено"
        )
    elif message.audio:
        audio = message.audio
        await competition.add_competition_media_file(competition_id, audio.file_id, "audio")

        await message.answer(
            f"Аудио {audio.file_name} добавлено"
        )
    elif message.document:
        document = message.document
        await competition.add_competition_media_file(competition_id, document.file_id, "document")

        await message.answer(
            f"Документ {document.file_name} добавлен"
        )

    else:
        await message.answer("Пришлите медиафайлы (фото, видео, аудио, документы), которые должны быть прикреплены к конкурсному сообщению")


async def send_demonstration(
        competition_schema: CompetitionSchema,
        message: Message,
        is_demo: bool = True
) -> None:
    competition_id = competition_schema.competition_id
    media_files = await competition.get_competition_media_files(competition_id)

    if media_files:
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

        media_group[0].caption = competition_schema.description

        await bot.send_media_group(
            chat_id=message.chat.id,
            media=media_group
        )
        await message.delete()
    else:
        if is_demo:
            await message.edit_text(
                text=competition_schema.description,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
                reply_markup=None,
            )
        else:
            await message.answer(
                text=competition_schema.description,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
