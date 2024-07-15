import random
import re
from datetime import datetime
from enum import Enum

from aiogram import Bot
from aiogram.types import Message, LinkPreviewOptions, InputMediaDocument, InputMediaAudio, \
    InputMediaVideo, InputMediaPhoto, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.main import post_message_db, bot, post_message_media_file_db, bot_db, contest_db, logger
from bot.utils import MessageTexts, excel_utils
from bot.config import WEB_APP_URL, WEB_APP_PORT
from bot.states import States
from bot.utils.keyboard_utils import make_webapp_info
from bot.enums.post_message_type import PostMessageType
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard
from bot.keyboards.channel_keyboards import InlineJoinContestKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard, ReplyBackPostMessageMenuKeyboard, \
    ReplyConfirmMediaFilesKeyboard, UnknownPostMessageType

from database.models.bot_model import BotSchema
from database.models.post_message_model import PostMessageSchema
from database.models.post_message_media_files import PostMessageMediaFileSchema

from logs.config import extra_params


def get_channel_id(state_data, post_message_type):
    if post_message_type in (PostMessageType.CHANNEL_POST, PostMessageType.CONTEST):
        return state_data["channel_id"]
    else:
        return None


class PostActionType(Enum):
    DEMO = "demo"  # Демо сообщение с главного бота
    # Демо сообщение с главного бота (но немного другой функионал для отправки)
    AFTER_REDACTING = "after_redacting"
    # Главная рассылка (отправка с кастомного бота всем пользователям)
    RELEASE = "release"


async def edit_media_files(
        message: Message,
        state: FSMContext,
        post_message_type: PostMessageType):
    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message = await post_message_db.get_post_message_by_bot_id(bot_id, post_message_type)
    post_message_id = post_message.post_message_id

    if (message.photo or message.video or message.audio or message.document) and "first" not in state_data:
        await post_message_media_file_db.delete_post_message_media_files(post_message_id)
        state_data["first"] = True

    match message.text:
        case ReplyConfirmMediaFilesKeyboard.Callback.ActionEnum.CONFIRM.value:
            return await _media_confirm(
                message,
                state,
                bot_id,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )

        case ReplyConfirmMediaFilesKeyboard.Callback.ActionEnum.CLEAR.value:
            return await _media_clear(message, post_message_id, post_message_type)
        case _:
            answer_text = await _media_save(message, post_message_id, post_message_type)
            if answer_text:
                await message.answer(answer_text)


async def _media_confirm(
        message: Message,
        state: FSMContext,
        bot_id: int,
        post_message_type,
        channel_id: int | None):
    state_data = await state.get_data()

    await _back_to_post_message_menu(message, bot_id, post_message_type, channel_id)
    await state.set_state(States.BOT_MENU)

    state_data.pop("first", None)
    return await state.set_data(state_data)


async def _media_clear(message: Message, post_message_id, post_message_type):
    await message.answer("Очищаем все файлы...")
    await post_message_media_file_db.delete_post_message_media_files(post_message_id=post_message_id)

    match post_message_type:
        case PostMessageType.MAILING:
            return await message.answer(
                "Отправьте одним сообщение медиафайлы для рассылочного сообщения\n\n"
                "❗ Старые медиафайлы к этому рассылочному сообщению <b>перезапишутся</b>\n\n"
                "❗❗ Обратите внимание, что к сообщению нельзя будет прикрепить кнопку, "
                "если медиафайлов <b>больше одного</b>",
                reply_markup=ReplyConfirmMediaFilesKeyboard.get_keyboard()
            )
        case PostMessageType.CHANNEL_POST:
            return await message.answer(
                "Отправьте одним сообщение медиафайлы для записи в канал\n\n"
                "❗ Старые медиафайлы к этому рассылочному сообщению <b>перезапишутся</b>\n\n"
                "❗❗ Обратите внимание, что к сообщению нельзя будет прикрепить кнопку, "
                "если медиафайлов <b>больше одного</b>",
                reply_markup=ReplyConfirmMediaFilesKeyboard.get_keyboard()
            )
        case PostMessageType.CONTEST:
            return await message.answer(
                "Отправьте одним сообщением <b>один</b> медиафайл для сообщения с конкурсом\n\n"
                "❗ Старый медиафайл к этой записи в канал <b>перезапишется</b>\n\n")
        case _:
            raise UnknownPostMessageType


async def _media_save(
        message: Message,
        post_message_id: int,
        post_message_type: PostMessageType) -> str | None:
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
        match post_message_type:
            case PostMessageType.MAILING:
                text = "Пришлите медиафайлы (фото, видео, аудио, документы), " \
                       "которые должны быть прикреплены к рассылочному сообщению"
            case PostMessageType.CHANNEL_POST:
                text = "Пришлите медиафайлы (фото, видео, аудио, документы), " \
                       "которые должны быть прикреплены к записи в канал"
            case PostMessageType.CONTEST:
                text = "Пришлите медиафайл (фото, видео, аудио, документ), " \
                       "который должен быть прикреплен к записи в канал"
            case _:
                raise UnknownPostMessageType

        await message.answer(
            text,
            reply_markup=ReplyConfirmMediaFilesKeyboard.get_keyboard()
        )
        return None

    if post_message_type == PostMessageType.CONTEST and \
            len(await post_message_media_file_db.get_all_post_message_media_files(post_message_id)) > 0:
        return "❗ Внимание, для конкурса был выбран только <b>один</b> медиафайл\n\n" \
               "Телеграм не позволяет отправлять кнопку, если в сообщении больше одного медиафайла"

    await post_message_media_file_db.add_post_message_media_file(PostMessageMediaFileSchema.model_validate(
        {"post_message_id": post_message_id, "file_id_main_bot": file_id,
         "file_path": file_path, "media_type": media_type}
    ))
    return answer_text


async def edit_button_text(
        message: Message,
        state: FSMContext,
        post_message_type: PostMessageType):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    post_message = await post_message_db.get_post_message(post_message_id)

    if not post_message.has_button:
        return await _reply_no_button(
            message,
            state,
            bot_id,
            post_message_type,
            channel_id=get_channel_id(state_data, post_message_type)
        )

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(
                message,
                bot_id,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )
        else:
            await _button_text_save(
                message,
                post_message,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer("Название кнопки должно содержать текст")


async def _button_text_save(
        message: Message,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    post_message.button_text = message.text

    await post_message_db.update_post_message(post_message)

    media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message.post_message_id)

    await message.answer(
        "Предпросмотр 👇",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(post_message.bot_id)
    )
    await send_post_message(
        bot,
        message.from_user.id,
        post_message,
        media_files,
        PostActionType.AFTER_REDACTING,
        message
    )

    custom_bot_token = (await bot_db.get_bot(post_message.bot_id)).token
    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageType

    await message.answer(
        MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            post_message.bot_id, post_message_type, channel_id
        )
    )


async def edit_message(
        message: Message,
        state: FSMContext,
        post_message_type: PostMessageType):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    post_message = await post_message_db.get_post_message(post_message_id)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(
                message,
                bot_id,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )
        else:
            await _message_save(
                message,
                post_message,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer(
            "Описание должно содержать текст.\n"
            "Если есть необходимость прикрепить медиафайлы, то для этого есть пункт в меню"
        )


async def edit_winners_count(
        message: Message,
        state: FSMContext,
        post_message_type: PostMessageType):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    post_message = await post_message_db.get_post_message(post_message_id)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(
                message,
                bot_id,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )
        else:
            try:
                int(message.text.strip())
            except ValueError:
                return await message.reply("Количество победителей должно быть целым числом.")
            await _winners_count_save(
                message,
                post_message,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer(
            "Количество победителей должно быть указано в тексте сообщения.\n"
            "Если есть необходимость прикрепить медиафайлы, то для этого есть пункт в меню"
        )


async def _winners_count_save(
        message: Message,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int
):
    contest = await contest_db.get_contest_by_bot_id(post_message.bot_id)
    contest.winners_count = int(message.text.strip())
    await contest_db.update_contest(contest)
    await message.answer(f"Количество победителей изменено на: <b>{contest.winners_count}</b>")

    custom_bot_token = (await bot_db.get_bot(post_message.bot_id)).token
    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case PostMessageType.CONTEST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageType

    await message.answer(
        MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            post_message.bot_id, post_message_type, channel_id
        )
    )


async def _message_save(
        message: Message,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    post_message.description = message.html_text
    media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message.post_message_id)

    await post_message_db.update_post_message(post_message)

    await message.answer(
        "Предпросмотр 👇",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(post_message.bot_id)
    )
    await send_post_message(
        bot,
        message.from_user.id,
        post_message,
        media_files,
        PostActionType.AFTER_REDACTING,
        message,
    )

    custom_bot_token = (await bot_db.get_bot(post_message.bot_id)).token
    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case PostMessageType.CONTEST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageType

    await message.answer(
        MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            post_message.bot_id, post_message_type, channel_id
        )
    )


async def edit_delay_date(
        message: Message,
        state: FSMContext,
        post_message_type: PostMessageType):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    post_message = await post_message_db.get_post_message(post_message_id)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(
                message,
                bot_id,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            try:
                result = await _delay_save(
                    message,
                    post_message,
                    post_message_type,
                    channel_id=get_channel_id(state_data, post_message_type)
                )
                if result:
                    await state.set_state(States.BOT_MENU)
                    await state.set_data(state_data)
            except ValueError:
                return await message.reply(
                    "Некорректный формат. Пожалуйста, "
                    "введите время и дату в правильном формате."
                )


async def edit_contest_finish_date(
        message: Message,
        state: FSMContext,
        post_message_type: PostMessageType):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    post_message = await post_message_db.get_post_message(post_message_id)

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(
                message,
                bot_id,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
        else:
            try:
                result = await _contest_finish_date_save(
                    message,
                    post_message,
                    post_message_type,
                    channel_id=get_channel_id(state_data, post_message_type)
                )
                if result:
                    await state.set_state(States.BOT_MENU)
                    await state.set_data(state_data)
            except ValueError:
                return await message.reply(
                    "Некорректный формат. Пожалуйста, "
                    "введите время и дату в правильном формате."
                )


async def pre_finish_contest(contest_id: int):
    contest = await contest_db.get_contest_by_contest_id(contest_id)
    db_bot = await bot_db.get_bot(contest.bot_id)
    contest_users = await contest_db.get_contest_users(contest_id)

    logger.info(f"finishing contest..., contest_id={contest_id}",
                extra_params(contest_id=contest_id, bot_id=db_bot.bot_id))

    if not contest_users:
        await bot.send_message(db_bot.created_by,
                               "😞 К сожалению в созданном конкурсе не было участников, "
                               "конкурс завершен без результатов.")
    else:
        if len(contest_users) <= contest.winners_count:
            await bot.send_message(db_bot.created_by, f"Количество участников конкурса ({len(contest_users)}) меньше "
                                                      f"или равна количеству победителей ({contest.winners_count}).\n\n"
                                                      f"Все участники конкурса стали победителями.")
            for user in contest_users:
                user.is_won = True
                await contest_db.update_contest_user(user)
        else:
            await bot.send_message(db_bot.created_by, "Выбираю случайных победителей...")
            winner_users = random.sample(contest_users, contest.winners_count)
            for user in winner_users:
                user.is_won = True
                await contest_db.update_contest_user(user)
        await excel_utils.send_contest_results_xlsx(contest_users, contest_id)

    contest.is_finished = True
    await contest_db.update_contest(contest)
    await post_message_db.delete_post_message(contest.post_message_id)


async def _contest_finish_date_save(
        message: Message,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
) -> bool:
    datetime_obj = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
    datetime_obj.replace(tzinfo=None)

    if datetime.now() > datetime_obj:
        await message.reply("Введенное время уже прошло. Введите, пожалуйста, <b>будущее</b> время")
        return False

    contest = await contest_db.get_contest_by_bot_id(bot_id=post_message.bot_id)

    contest.finish_date = datetime_obj

    await contest_db.update_contest(contest)

    await message.reply(
        f"Дата окончания конкурса установлена на: <b>{datetime_obj.strftime('%Y-%m-%d %H:%M')}</b>",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(post_message.bot_id)
    )

    custom_bot_token = (await bot_db.get_bot(post_message.bot_id)).token
    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageType

    await message.answer(
        MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            post_message.bot_id, post_message_type, channel_id
        )
    )

    return True


async def _delay_save(
        message: Message,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
) -> bool:
    datetime_obj = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
    datetime_obj.replace(tzinfo=None)

    if datetime.now() > datetime_obj:
        await message.reply("Введенное время уже прошло. Введите, пожалуйста, <b>будущее</b> время")
        return False

    post_message.is_delayed = True
    post_message.send_date = datetime_obj

    await post_message_db.update_post_message(post_message)

    await message.reply(
        f"Запланировано на: <b>{datetime_obj.strftime('%Y-%m-%d %H:%M')}</b>\n\n"
        f"Для отложенного запуска нажмите <b>Запустить</b> в меню",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(post_message.bot_id)
    )

    custom_bot_token = (await bot_db.get_bot(post_message.bot_id)).token
    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageType

    await message.answer(
        MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            post_message.bot_id, post_message_type, channel_id
        )
    )

    return True


async def edit_button_url(
        message: Message,
        state: FSMContext,
        post_message_type: PostMessageType):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    post_message_id = state_data["post_message_id"]

    post_message = await post_message_db.get_post_message(post_message_id)

    if not post_message.has_button:
        return await _reply_no_button(
            message,
            state,
            bot_id,
            post_message_type,
            channel_id=get_channel_id(state_data, post_message_type)
        )

    if message_text:
        if message_text == ReplyBackPostMessageMenuKeyboard.Callback.ActionEnum.BACK_TO_POST_MESSAGE_MENU.value:
            await _back_to_post_message_menu(
                message,
                bot_id,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )
        else:
            pattern = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+" \
                      r"|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
            if not re.fullmatch(pattern, message.text):
                return await message.answer(
                    "Невалидная ссылка. Введите, пожалуйста, ссылку в стандартном формате, "
                    "начинающемся с <b>http</b> или <b>https</b>"
                )

            await _button_url_save(
                message,
                post_message,
                post_message_type,
                channel_id=get_channel_id(state_data, post_message_type)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
    else:
        await message.answer("Ссылка должна содержать только текст")


async def _button_url_save(
        message: Message,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    post_message.button_url = message.text
    media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message.post_message_id)
    await post_message_db.update_post_message(post_message)

    await message.answer(
        "Предпросмотр 👇",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(post_message.bot_id)
    )
    await send_post_message(
        bot,
        message.from_user.id,
        post_message,
        media_files,
        PostActionType.AFTER_REDACTING,
        message
    )

    custom_bot_token = (await bot_db.get_bot(post_message.bot_id)).token
    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageType

    await message.answer(
        MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            post_message.bot_id, post_message_type, channel_id
        )
    )


async def send_post_message(
        bot_from_send: Bot | BotSchema,
        to_chat_id: int,
        post_message_schema: PostMessageSchema,
        media_files: list[PostMessageMediaFileSchema],
        post_action_type: PostActionType,
        message: Message = None
) -> None:
    if isinstance(bot_from_send, BotSchema):
        bot_from_send = Bot(bot_from_send.token)

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
        if post_message_schema.post_message_type == PostMessageType.CONTEST:
            keyboard = await InlineJoinContestKeyboard.get_keyboard(bot_id=post_message_schema.bot_id,
                                                                    contest_members_count=0,
                                                                    post_message_id=post_message_schema.post_message_id)

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
                chat_id=to_chat_id,
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
                to_chat_id,
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
                chat_id=to_chat_id,
                text=post_message_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    post_message_schema.enable_notification_sound),
                link_preview_options=LinkPreviewOptions(is_disabled=not (
                    post_message_schema.enable_link_preview))
            )
        else:
            await bot_from_send.send_message(
                chat_id=to_chat_id,
                text=post_message_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    post_message_schema.enable_notification_sound),
                link_preview_options=LinkPreviewOptions(is_disabled=not (
                    post_message_schema.enable_link_preview))
            )


async def _reply_no_button(
        message: Message,
        state: FSMContext,
        bot_id: int,
        post_message_type: PostMessageType,
        channel_id: int | None
) -> None:
    state_data = await state.get_data()

    await message.answer(
        "В настраиваемом сообщении кнопки уже нет",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
    )

    custom_bot_token = (await bot_db.get_bot(bot_id)).token
    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageType

    await message.answer(
        post_message_type.value.format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            bot_id, post_message_type, channel_id
        )
    )

    await state.set_state(States.BOT_MENU)
    await state.set_data(state_data)


async def _back_to_post_message_menu(
        message: Message,
        bot_id: int,
        post_message_type: PostMessageType,
        channel_id: int | None
) -> None:
    await message.answer(
        "Возвращаемся в меню...",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
    )

    custom_bot_token = (await bot_db.get_bot(bot_id)).token
    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageType

    await message.answer(
        text=MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            bot_id, post_message_type, channel_id
        )
    )
