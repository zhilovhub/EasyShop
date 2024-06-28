from datetime import datetime, timedelta

from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.main import _scheduler, custom_bot_user_db, post_message_media_file_db, channel_user_db
from bot.utils import MessageTexts
from bot.keyboards import *
from bot.states.states import States
from bot.handlers.routers import channel_menu_router
from bot.post_message.post_message_editors import edit_button_url, PostMessageType, edit_delay_date, edit_message, \
    edit_button_text, edit_media_files, send_post_message
from bot.post_message.post_message_handler import post_message_handler
from bot.keyboards.channel_keyboards import ReplyBackChannelMenuKeyboard, InlineChannelsListKeyboard, \
    InlineChannelMenuKeyboard
from bot.keyboards.main_menu_keyboards import InlineBotMenuKeyboard, ReplyBotMenuKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard

from database.models.channel_model import ChannelNotFound
from database.models.channel_post_model import ChannelPostSchemaWithoutId
from database.models.post_message_model import PostMessageSchemaWithoutId


@channel_menu_router.callback_query(lambda query: InlineChannelsListKeyboard.callback_validator(query.data))
async def channels_list_callback_handler(query: CallbackQuery):
    callback_data = InlineChannelsListKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id
    custom_bot = await bot_db.get_bot(bot_id)
    custom_tg_bot = Bot(custom_bot.token)

    match callback_data.a:
        case callback_data.ActionEnum.OPEN_CHANNEL:
            channel_id = callback_data.channel_id
            channel_username = (await custom_tg_bot.get_chat(channel_id)).username
            await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(
                    channel_username,
                    (await custom_tg_bot.get_me()).username
                ),
                reply_markup=await InlineChannelMenuKeyboard.get_keyboard(custom_bot.bot_id, channel_id)
            )
        case callback_data.ActionEnum.BACK_TO_MAIN_MENU:
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id),
                parse_mode=ParseMode.HTML
            )


@channel_menu_router.callback_query(lambda query: InlineChannelMenuKeyboard.callback_validator(query.data))
async def channel_menu_callback_handler(query: CallbackQuery):
    callback_data = InlineChannelMenuKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id
    channel_id = callback_data.channel_id

    custom_bot = await bot_db.get_bot(bot_id)
    custom_tg_bot = Bot(custom_bot.token)
    custom_bot_username = (await custom_tg_bot.get_me()).username

    channel_username = (await custom_tg_bot.get_chat(channel_id)).username

    match callback_data.a:
        case callback_data.ActionEnum.ANALYTICS:
            plus_users = await channel_user_db.get_joined_channel_users_by_channel_id(channel_id)
            minus_users = await channel_user_db.get_left_channel_users_by_channel_id(channel_id)

            await query.answer(
                text=f"Прирост подписчиков в канале @{channel_username}: {len(plus_users) - len(minus_users)}\n\n"
                     f"Отписалось - {len(minus_users)}\n"
                     f"Подписалось - {len(plus_users)}\n",
                show_alert=True
            )
        case callback_data.ActionEnum.LEAVE_CHANNEL:
            leave_result = await custom_tg_bot.leave_chat(chat_id=channel_id)

            if leave_result:
                await query.message.answer(f"Вышел из канала @{channel_username}")
            else:
                await query.message.answer(f"Произошла ошибка при выходе из канала @{channel_username}")
            await query.message.edit_text(
                MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlineChannelsListKeyboard.get_keyboard(custom_bot.bot_id)
            )
        case callback_data.ActionEnum.CREATE_POST_MESSAGE | callback_data.ActionEnum.EDIT_POST_MESSAGE:
            try:
                channel_post = await channel_post_db.get_channel_post_by_bot_id(bot_id=bot_id)
                await query.answer("Запись уже создана", show_alert=True)
            except ChannelPostNotFound:
                channel_post = None

            if not channel_post and callback_data.a == callback_data.ActionEnum.CREATE_POST_MESSAGE:
                post_message_id = await post_message_db.add_post_message(PostMessageSchemaWithoutId.model_validate(
                    {"bot_id": bot_id, "created_at": datetime.now().replace(tzinfo=None)}
                ))
                await channel_post_db.add_channel_post(ChannelPostSchemaWithoutId.model_validate(
                    {"bot_id": bot_id, "post_message_id": post_message_id}
                ))

            await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(channel_username),
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                    bot_id=bot_id,
                    post_message_type=PostMessageType.CHANNEL_POST
                )
            )


@channel_menu_router.callback_query(lambda query: InlinePostMessageMenuKeyboard.callback_validator(query.data))
async def channel_post_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    await post_message_handler(query, state)


@channel_menu_router.callback_query(lambda query: query.data.startswith("channel_menu"))
async def channel_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    query_data = query.data.split(":")

    # Standart fields
    action = query_data[1]
    bot_id = int(query_data[2])
    channel_id = int(query_data[3])

    custom_bot = await bot_db.get_bot(bot_id)
    custom_tg_bot = Bot(custom_bot.token)
    custom_bot_username = (await custom_tg_bot.get_me()).username

    channel_username = (await custom_tg_bot.get_chat(channel_id)).username

    # Detect if we have requested channel in db
    try:
        await channel_db.get_channel(channel_id=channel_id)
    except ChannelNotFound:
        await query.answer("Канал удален", show_alert=True)
        return query.message.delete()

    # TODO Fix with post_type parameter in state_data
    # Channel Post Validation:
    # Temp variables to detect which type of request we recieve
    is_running = False
    channel_post = None

    # if requested object is contest post, len(query_data) will have 5 fields (last one "channel_post_id")
    # if requested object is reqular post or creation request, len(query_data) will have 4 fields

    if len(query_data) > 4:
        # Searching for contest object
        try:
            channel_post = await channel_post_db.get_channel_post(channel_id, is_contest=True)
            is_running = channel_post.is_running
        except ChannelPostNotFound:
            pass
    else:
        # Searching for regular post object
        # (if not found, channel_post will still be None, so we surely know that it is createion request)
        try:
            channel_post = await channel_post_db.get_channel_post(channel_id, is_contest=False)
            is_running = channel_post.is_running
        except ChannelPostNotFound:
            pass
    # If we found requested object and it is running now we can only stop it
    if is_running is True:
        match action:
            case "stop_post":
                custom_users_length = len(await custom_bot_user_db.get_custom_bot_users(bot_id=bot_id))

                channel_post.is_running = False
                try:
                    await _scheduler.del_job_by_id(channel_post.job_id)
                except:
                    logger.warning(
                        f"Job ID {channel_post.job_id} not found")
                channel_post.job_id = None
                await channel_post_db.update_channel_post(channel_post)
                await query.message.answer(f"Отправка поста остановлена")

                await query.message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotMenuKeyboard.get_keyboard(bot_id)
                )
                return await query.message.delete()
            case _:
                if channel_post.is_contest:
                    await query.answer("Сейчас в канале есть активный конкурс, дождитесь когда он закончится",
                                       show_alert=True)
                else:
                    await query.answer("Пост уже в очереди", show_alert=True)
                await query.message.answer(
                    text=MessageTexts.BOT_CHANNEL_POST_MENU_WHILE_RUNNING.value.format(
                        channel_username),
                    reply_markup=await get_inline_bot_channel_post_menu_keyboard(
                        bot_id, channel_id, is_contest=channel_post.is_contest)
                )
                return await query.message.delete()

    # Works only if we get requested object from db
    match action:
        case "back_to_channels_list":
            await query.message.edit_text(
                text=MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format(
                    custom_bot_username),
                reply_markup=await InlineChannelsListKeyboard.get_keyboard(bot_id)
            )
        case "back_to_channel_list":
            await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(channel_username,
                                                                   (await custom_tg_bot.get_me()).username),
                reply_markup=await InlineChannelMenuKeyboard.get_keyboard(custom_bot.bot_id, channel_id)
            )
        case "accept_start":
            media_files = await post_message_media_file_db.get_all_channel_post_media_files(
                channel_post_id=channel_post.channel_post_id)

            if len(media_files) > 1 and channel_post.has_button:
                await query.answer(
                    "Telegram не позволяет прикрепить кнопку, если в сообщении минимум 2 медиафайла",
                    show_alert=True
                )
            elif not media_files and not channel_post.description:
                return await query.answer(
                    text="В Вашем рассылочном сообщении нет ни текста, ни медиафайлов",
                    show_alert=True
                )
            if channel_post.is_contest:
                if channel_post.contest_end_date is None:
                    return await query.answer(
                        text="Не установлен конец конкурса",
                        show_alert=True
                    )
                elif channel_post.contest_winner_amount is None:
                    return await query.answer(
                        text="Не установлено количество победителей",
                        show_alert=True
                    )
                elif channel_post.contest_end_date < (timedelta(minutes=2) + datetime.now()):
                    return await query.answer(
                        text="Дата окончания конкурса уже прошла",
                        show_alert=True
                    )
            if channel_post.description or media_files:
                if channel_post.is_delayed:
                    # Небольшой запас по времени
                    if datetime.now() > (channel_post.send_date + timedelta(minutes=2)):
                        await query.answer(
                            text="Указанное время отправки уже прошло",
                            show_alert=True
                        )
                        return
                channel_post.is_running = True
                await channel_post_db.update_channel_post(channel_post)

                text = f"Рассылка начнется в {channel_post.send_date}" if channel_post.is_delayed else "Отправляю пост"
                await query.message.answer(text)
                if channel_post.is_delayed:
                    await query.message.answer(
                        text=MessageTexts.BOT_CHANNEL_POST_MENU_WHILE_RUNNING.value.format(
                            channel_username),
                        reply_markup=await get_inline_bot_channel_post_menu_keyboard(
                            bot_id, channel_id, channel_post.is_contest)
                    )

                if not (channel_post.is_delayed):
                    await send_post_message(
                        bot_from_send=custom_bot,
                        to_user_id=channel_post.channel_id,
                        channel_post_schema=channel_post,
                        media_files=media_files,
                        mailing_message_type=MailingMessageType.RELEASE,
                        chat_id=query.from_user.id,
                        message_id=query.message.message_id,
                    )
                    await query.message.edit_text(
                        MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(channel_username,
                                                                           (await custom_tg_bot.get_me()).username),
                        reply_markup=await InlineChannelMenuKeyboard.get_keyboard(custom_bot.bot_id, channel_id)
                    )
                else:
                    job_id = await _scheduler.add_scheduled_job(
                        func=send_post_message, run_date=channel_post.send_date,
                        args=[custom_bot, channel_post.channel_id, channel_post, media_files,
                              MailingMessageType.RELEASE, query.from_user.id, query.message.message_id])
                    channel_post.job_id = job_id
                    await channel_post_db.update_channel_post(channel_post)
            else:
                await query.answer(
                    text="В Вашем рассылочном сообщении нет ни текста, ни медиафайлов",
                    show_alert=True
                )
        case "back_to_editing_channel_post":
            return await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                    channel_username),
                reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id,
                                                                             is_contest=channel_post.is_contest)
            )


@channel_menu_router.message(StateFilter(
    States.EDITING_POST_DELAY_DATE,
    States.EDITING_POST_TEXT,
    States.EDITING_POST_BUTTON_TEXT,
    States.EDITING_POST_BUTTON_URL,
    States.EDITING_POST_MEDIA_FILES,
))
async def editing_post_message_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()

    match current_state:
        case States.EDITING_POST_DELAY_DATE:
            await edit_delay_date(message, state, PostMessageType.CHANNEL_POST)
        case States.EDITING_POST_TEXT:
            await edit_message(message, state, PostMessageType.CHANNEL_POST)
        case States.EDITING_POST_BUTTON_TEXT:
            await edit_button_text(message, state, PostMessageType.CHANNEL_POST)
        case States.EDITING_POST_BUTTON_URL:
            await edit_button_url(message, state, PostMessageType.CHANNEL_POST)
        case States.EDITING_POST_MEDIA_FILES:
            await edit_media_files(message, state, PostMessageType.CHANNEL_POST)
