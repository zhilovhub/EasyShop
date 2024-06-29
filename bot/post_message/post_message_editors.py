import re
from datetime import datetime
from enum import Enum

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, LinkPreviewOptions, InputMediaDocument, InputMediaAudio, \
    InputMediaVideo, InputMediaPhoto, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.main import bot_db, post_message_db, bot, post_message_media_file_db
from bot.utils import MessageTexts
from bot.config import WEB_APP_URL, WEB_APP_PORT
from bot.states import States
from bot.utils.keyboard_utils import make_webapp_info
from bot.enums.post_message_type import PostMessageType
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard, ReplyBackPostMessageMenuKeyboard, \
    ReplyConfirmMediaFilesKeyboard

from database.models.post_message_model import PostMessageSchema
from database.models.post_message_media_files import PostMessageMediaFileSchema


class PostActionType(Enum):
    DEMO = "demo"  # Демо сообщение с главного бота
    # Демо сообщение с главного бота (но немного другой функионал для отправки)
    AFTER_REDACTING = "after_redacting"
    # Главная рассылка (отправка с кастомного бота всем пользователям)
    RELEASE = "release"


async def edit_media_files(message: Message, state: FSMContext, post_message_type: PostMessageType):
    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message = await post_message_db.get_post_message_by_bot_id(bot_id, post_message_type)
    post_message_id = post_message.post_message_id

    if (message.photo or message.video or message.audio or message.document) and "first" not in state_data:
        await post_message_media_file_db.delete_post_message_media_files(post_message_id)
        state_data["first"] = True

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    match message.text:
        case ReplyConfirmMediaFilesKeyboard.Callback.ActionEnum.CONFIRM.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username, post_message_type)

            await state.set_state(States.BOT_MENU)
            return await state.set_data(state_data)

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


async def edit_button_text(message: Message, state: FSMContext, post_message_type: PostMessageType):
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
            await _back_to_post_message_menu(message, bot_id, custom_bot_username, post_message_type)
        else:
            post_message.button_text = message.text

            await post_message_db.update_post_message(post_message)

            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            await send_post_message(  # TODO was send_channel_post_message
                bot,
                message.from_user.id,
                post_message,
                media_files,
                PostActionType.AFTER_REDACTING,
                message
            )

            await message.answer(
                MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer("Название кнопки должно содержать текст")


async def edit_message(message: Message, state: FSMContext, post_message_type: PostMessageType):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    post_message = await post_message_db.get_post_message(post_message_id)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username, post_message_type)
        else:
            post_message.description = message.html_text
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

            await post_message_db.update_post_message(post_message)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            await send_post_message(  # TODO was send_channel_post_message
                bot,
                message.from_user.id,
                post_message,
                media_files,
                PostActionType.AFTER_REDACTING,
                message,
            )

            await message.answer(
                MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer(
            "Описание должно содержать текст.\n"
            "Если есть необходимость прикрепить медиафайлы, то для этого есть пункт в меню"
        )


async def edit_delay_date(message: Message, state: FSMContext, post_message_type: PostMessageType):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    post_message = await post_message_db.get_post_message(post_message_id)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username, post_message_type)
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
                    f"Для отложенного запуска нажмите <b>Запустить</b> в меню",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
                )

                await message.answer(
                    MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type)
                )

                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)

            except ValueError:
                return await message.reply(
                    "Некорректный формат. Пожалуйста, "
                    "введите время и дату в правильном формате."
                )


async def edit_button_url(message: Message, state: FSMContext, post_message_type: PostMessageType):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data[post_message_type.value[0]]

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    post_message = await post_message_db.get_post_message(post_message_id)

    if not post_message.has_button:
        return await _reply_no_button(message, bot_id, custom_bot_username, state, post_message_type)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(message, bot_id, custom_bot_username, post_message_type)
        else:
            pattern = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+" \
                      r"|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
            if not re.fullmatch(pattern, message.text):
                return await message.answer(
                    "Невалидная ссылка. Введите, пожалуйста, ссылку в стандартном формате, "
                    "начинающемся с <b>http</b> или <b>https</b>"
                )

            post_message.button_url = message.text
            media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)
            await post_message_db.update_post_message(post_message)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
            )
            # TODO can be this
            # await send_channel_post_message(
            #     bot,
            #     message.from_user.id,
            #     channel_post,
            #     media_files,
            #     MailingMessageType.AFTER_REDACTING,
            #     message.from_user.id,
            #     message.message_id,
            # )
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
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer("Ссылка должна содержать только текст")


async def send_post_message(
        bot_from_send: Bot,
        to_user_id: int,
        post_message_schema: PostMessageSchema,
        media_files: list[PostMessageMediaFileSchema],
        post_action_type: PostActionType,
        message: Message = None,
) -> None:
    if post_message_schema.has_button:
        if post_message_schema.button_url == f"{WEB_APP_URL}:{WEB_APP_PORT}" \
                                             f"/products-page/?bot_id={post_message_schema.bot_id}":
            button = InlineKeyboardButton(
                text=post_message_schema.button_text,
                web_app=make_webapp_info(bot_id=post_message_schema.bot_id)
            )
        else:
            button = InlineKeyboardButton(
                text=post_message_schema.button_text,
                url=post_message_schema.button_url
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
            if post_action_type == PostActionType.RELEASE:
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
            if post_message_schema.description:
                media_group[0].caption = post_message_schema.description

            uploaded_media_files.extend(await bot_from_send.send_media_group(
                chat_id=to_user_id,
                media=media_group,
                disable_notification=not post_message_schema.enable_link_preview,
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
                caption=post_message_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    post_message_schema.enable_notification_sound),
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
                await post_message_media_file_db.update_media_file(old_message)
    else:
        if post_message_schema.description is None:
            return
        if post_action_type == PostActionType.DEMO:  # только при демо с главного бота срабатывает
            await message.edit_text(
                text=post_message_schema.description,
                link_preview_options=LinkPreviewOptions(is_disabled=not (
                    post_message_schema.enable_link_preview)),
                reply_markup=keyboard,
            )
        elif post_action_type == PostActionType.AFTER_REDACTING:
            await bot_from_send.send_message(
                chat_id=to_user_id,
                text=post_message_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    post_message_schema.enable_notification_sound),
                link_preview_options=LinkPreviewOptions(is_disabled=not (
                    post_message_schema.enable_link_preview))
            )
        else:
            await bot_from_send.send_message(
                chat_id=to_user_id,
                text=post_message_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    post_message_schema.enable_notification_sound),
                link_preview_options=LinkPreviewOptions(is_disabled=not (
                    post_message_schema.enable_link_preview))
            )


async def _inline_no_button(
        query: CallbackQuery,
        bot_id: int,
        custom_bot_username: str,
        post_message_type: PostMessageType
) -> None:
    await query.answer(
        "В этом рассылочном сообщении кнопки нет", show_alert=True
    )
    await query.message.edit_text(
        text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type),
        parse_mode=ParseMode.HTML
    )


async def _reply_no_button(
        message: Message,
        bot_id: int,
        object_username: str,
        state: FSMContext,
        post_message_type: PostMessageType
) -> None:
    state_data = await state.get_data()

    await message.answer(
        "В настраиваемом сообщении кнопки уже нет",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
    )
    await message.answer(
        post_message_type.value[1].format(object_username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type)
    )

    await state.set_state(States.BOT_MENU)
    await state.set_data(state_data)


async def _inline_back_to_post_message_menu(
        query: CallbackQuery,
        bot_id: int,
        custom_bot_username: str,
        post_message_type: PostMessageType
) -> None:
    await query.message.edit_text(
        text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(custom_bot_username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type),
        parse_mode=ParseMode.HTML
    )


async def _back_to_post_message_menu(
        message: Message,
        bot_id: int,
        object_username: str,
        post_message_type: PostMessageType,
) -> None:
    await message.answer(
        "Возвращаемся в меню...",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
    )
    await message.answer(
        text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(object_username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(bot_id, post_message_type)
    )


async def _is_post_message_valid(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        media_files: list[PostMessageMediaFileSchema]
) -> bool:
    if len(media_files) > 1 and post_message.has_button:
        await query.answer(
            "Telegram не позволяет прикрепить кнопку, если в сообщении минимум 2 медиафайла",
            show_alert=True
        )
        return False
    elif not media_files and not post_message.description:
        await query.answer(
            text="В Вашем рассылочном сообщении нет ни текста, ни медиафайлов",
            show_alert=True
        )
        return False

    return True