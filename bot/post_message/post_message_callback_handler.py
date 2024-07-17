from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.main import bot, _scheduler
from bot.utils import MessageTexts
from bot.states import States
from bot.graphs.graphs import generate_contest_users_graph
from bot.keyboards.channel_keyboards import InlineChannelMenuKeyboard
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard
from bot.post_message.post_message_utils import is_post_message_valid
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard, ReplyBackPostMessageMenuKeyboard, \
    ReplyConfirmMediaFilesKeyboard, InlinePostMessageAcceptDeletingKeyboard, InlinePostMessageExtraSettingsKeyboard, \
    InlinePostMessageStartConfirmKeyboard, UnknownPostMessageType
from bot.post_message.post_message_editors import send_post_message, pre_finish_contest, PostActionType

from common_utils.env_config import WEB_APP_URL, WEB_APP_PORT
from common_utils.keyboards.keyboards import InlineBotMenuKeyboard

from database.config import custom_bot_user_db, bot_db, post_message_db, contest_db, post_message_media_file_db
from database.models.post_message_model import PostMessageSchema, PostMessageType

from logs.config import extra_params, logger


class ContestMessageDontNeedButton(Exception):
    pass


def get_channel_id(callback_data, post_message_type):
    if post_message_type in (PostMessageType.CHANNEL_POST, PostMessageType.CONTEST):
        return callback_data.channel_id
    else:
        return None


async def _cancel_send(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        user_id: int,
        channel_id: int | None,
        contest_pre_finish: bool = False,
):
    custom_users_length = len(await custom_bot_user_db.get_custom_bot_users(bot_id=post_message.bot_id))

    post_message.is_running = False

    try:
        await _scheduler.del_job_by_id(post_message.job_id)
    except Exception as e:
        logger.warning(
            f"user_id={user_id}: Job ID {post_message.job_id} not found",
            extra=extra_params(
                user_id=user_id,
                bot_id=post_message.bot_id,
                post_message_id=post_message.post_message_id
            ),
            exc_info=e
        )

    post_message.job_id = None

    custom_bot = await bot_db.get_bot(post_message.bot_id)
    custom_bot_token = custom_bot.token
    custom_bot_username = (await Bot(custom_bot_token).get_me()).username

    match post_message_type:
        case PostMessageType.MAILING:
            await post_message_db.delete_post_message(post_message.post_message_id)
            await query.message.answer(
                f"Рассылка остановлена\nСообщений разослано - "
                f"{post_message.sent_post_message_amount}/{custom_users_length}",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(post_message.bot_id)
            )
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(post_message.bot_id),
                parse_mode=ParseMode.HTML
            )
        case PostMessageType.CHANNEL_POST:
            await post_message_db.delete_post_message(post_message.post_message_id)

            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
            await query.message.answer(
                f"Отправка записи отменена",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(post_message.bot_id)
            )
            await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(username, custom_bot_username),
                reply_markup=await InlineChannelMenuKeyboard.get_keyboard(post_message.bot_id, channel_id),
                parse_mode=ParseMode.HTML
            )
        case PostMessageType.CONTEST:
            contest = await contest_db.get_contest_by_bot_id(bot_id=post_message.bot_id)
            contest_users = await contest_db.get_contest_users(contest.contest_id)
            contest.is_finished = True
            path_to_graph = await generate_contest_users_graph(contest.contest_id)
            if contest.finish_job_id:
                try:
                    await _scheduler.del_job(contest.finish_job_id)
                except:  # noqa
                    pass

            username = (await Bot(custom_bot_token).get_chat(channel_id)).username

            if contest_pre_finish:
                await bot.send_message(custom_bot.created_by, "Досрочно завершаю конкурс...")
                await pre_finish_contest(contest.contest_id)
            else:
                await post_message_db.delete_post_message(post_message.post_message_id)
                await query.message.answer(
                    f"Конкурс отменен",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(post_message.bot_id)
                )
            await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(username, custom_bot_username),
                reply_markup=await InlineChannelMenuKeyboard.get_keyboard(post_message.bot_id, channel_id),
                parse_mode=ParseMode.HTML
            )

            if contest_users:
                await query.message.answer_photo(
                    FSInputFile(path_to_graph),
                    caption="📈 График количества участников конкурса от времени"
                )
        case _:
            raise UnknownPostMessageType


async def _button_add(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    custom_bot_token = (await bot_db.get_bot(post_message.bot_id)).token
    custom_bot = Bot(custom_bot_token)

    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
        case _:
            raise UnknownPostMessageType

    media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message.post_message_id)

    if post_message.has_button:
        await query.answer(MessageTexts.bot_post_button_already_exists_message(post_message_type), show_alert=True)
        await query.message.edit_text(
            text=MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                post_message.bot_id, post_message_type, channel_id
            ),
            parse_mode=ParseMode.HTML
        )
    elif len(media_files) > 1:
        await query.answer(
            "Кнопку нельзя добавить, если в сообщении больше одного медиафайла",
            show_alert=True
        )
    else:
        post_message.button_text = "Shop"
        match post_message_type:
            case PostMessageType.MAILING:
                post_message.button_url = f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id={post_message.bot_id}"
            case PostMessageType.CHANNEL_POST:
                post_message.button_url = f"t.me/{(await custom_bot.get_me()).username}/?start=web_app"
            case PostMessageType.CONTEST:
                raise ContestMessageDontNeedButton
            case _:
                raise UnknownPostMessageType
        post_message.has_button = True

        await post_message_db.update_post_message(post_message)

        await query.message.delete()
        await query.message.answer(
            "Кнопка добавлена\n\n"
            f"Сейчас там стандартный текст '{post_message.button_text}' и ссылка на Ваш магазин.\n"
            "Эти два параметры Вы можете изменить в настройках кнопки"
        )

        await query.message.answer(
            text=MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                post_message.bot_id, post_message_type, channel_id
            )
        )


async def _button_url(
        query: CallbackQuery,
        state: FSMContext,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    bot_id = post_message.bot_id

    if not post_message.has_button:
        await _inline_no_button(
            query,
            bot_id,
            post_message_type,
            channel_id=channel_id
        )
    else:
        await query.message.answer(
            "Введите ссылку, которая будет открываться у пользователей по нажатии на кнопку",
            reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
        )
        await query.answer()
        await state.set_state(States.EDITING_POST_BUTTON_URL)
        await state.set_data({
            "bot_id": bot_id,
            "channel_id": channel_id,
            "post_message_id": post_message.post_message_id,
            "post_message_type": post_message_type.value
        })


async def _button_text(
        query: CallbackQuery,
        state: FSMContext,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    bot_id = post_message.bot_id

    if not post_message.has_button:
        await _inline_no_button(
            query,
            bot_id,
            post_message_type,
            channel_id=channel_id
        )
    else:
        await query.message.answer(
            "Введите текст, который будет отображаться на кнопке",
            reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
        )
        await query.answer()
        await state.set_state(States.EDITING_POST_BUTTON_TEXT)
        await state.set_data({
            "bot_id": bot_id,
            "channel_id": channel_id,
            "post_message_id": post_message.post_message_id,
            "post_message_type": post_message_type.value
        })


async def _button_delete(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    bot_id = post_message.bot_id

    if not post_message.has_button:
        await _inline_no_button(
            query,
            bot_id,
            post_message_type,
            channel_id=channel_id
        )
    else:
        post_message.button_text = None
        post_message.button_url = None
        post_message.has_button = False

        await post_message_db.update_post_message(post_message)

        await query.message.delete()
        await query.message.answer("Кнопка удалена")

        custom_bot_token = (await bot_db.get_bot(bot_id)).token

        match post_message_type:
            case PostMessageType.MAILING:
                username = (await Bot(custom_bot_token).get_me()).username
            case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
                username = (await Bot(custom_bot_token).get_chat(channel_id)).username
            case _:
                raise UnknownPostMessageType

        await query.message.answer(
            text=MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                bot_id, post_message_type, channel_id
            )
        )


async def _post_message_text(
        query: CallbackQuery,
        state: FSMContext,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    match post_message_type:
        case PostMessageType.MAILING:
            text = "Введите текст, который будет отображаться в рассылочном сообщении"
        case PostMessageType.CHANNEL_POST:
            text = "Введите текст, который будет отображаться в записи для канала"
        case PostMessageType.CONTEST:
            text = "Введите текст, который будет отображаться в сообщении конкурса в канале"
        case _:
            raise UnknownPostMessageType

    await query.message.answer(
        text,
        reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
    )
    await query.answer()

    await state.set_state(States.EDITING_POST_TEXT)
    await state.set_data({
        "bot_id": post_message.bot_id,
        "channel_id": channel_id,
        "post_message_id": post_message.post_message_id,
        "post_message_type": post_message_type.value
    })


async def _contest_winners_count(
        query: CallbackQuery,
        state: FSMContext,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int
):
    text = "Введите количество победителей конкурса. (необходимо отправить целое число)"

    await query.message.answer(
        text,
        reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
    )
    await query.answer()

    await state.set_state(States.EDITING_CONTEST_WINNERS_COUNT)
    await state.set_data({
        "bot_id": post_message.bot_id,
        "channel_id": channel_id,
        "post_message_id": post_message.post_message_id,
        "post_message_type": post_message_type.value
    })


async def _contest_finish_date(
        query: CallbackQuery,
        state: FSMContext,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int
):
    text = MessageTexts.show_date_rules(name="завершения конкурса")

    await query.message.answer(
        text,
        reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
    )
    await query.answer()

    await state.set_state(States.EDITING_CONTEST_FINISH_DATE)
    await state.set_data({
        "bot_id": post_message.bot_id,
        "channel_id": channel_id,
        "post_message_id": post_message.post_message_id,
        "post_message_type": post_message_type.value
    })


async def _post_message_media(
        query: CallbackQuery,
        state: FSMContext,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    match post_message_type:
        case PostMessageType.MAILING:
            text = "Отправьте одним сообщение медиафайлы для рассылочного сообщения\n\n" \
                   "❗ Старые медиафайлы к этому рассылочному сообщению <b>перезапишутся</b>\n\n" \
                   "❗❗ Обратите внимание, что к сообщению нельзя будет прикрепить кнопку, " \
                   "если медиафайлов <b>больше одного</b>"
        case PostMessageType.CHANNEL_POST:
            text = "Отправьте одним сообщение медиафайлы для записи в канал\n\n" \
                   "❗ Старые медиафайлы к этой записи в канал <b>перезапишутся</b>\n\n" \
                   "❗❗ Обратите внимание, что к сообщению нельзя будет прикрепить кнопку, " \
                   "если медиафайлов <b>больше одного</b>"
        case PostMessageType.CONTEST:
            text = "Отправьте одним сообщением <b>один</b> медиафайл для сообщения с конкурсом\n\n" \
                   "❗ Старый медиафайл к этой записи в канал <b>перезапишется</b>\n\n"
        case _:
            raise UnknownPostMessageType

    await query.message.answer(
        text,
        reply_markup=ReplyConfirmMediaFilesKeyboard.get_keyboard()
    )
    await query.answer()

    await state.set_state(States.EDITING_POST_MEDIA_FILES)
    await state.set_data({
        "bot_id": post_message.bot_id,
        "channel_id": channel_id,
        "post_message_id": post_message.post_message_id,
        "post_message_type": post_message_type.value
    })


async def _start(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    post_message_id = post_message.post_message_id
    bot_id = post_message.bot_id
    media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

    if await is_post_message_valid(query, post_message, post_message_type, media_files):
        custom_bot_token = (await bot_db.get_bot(bot_id)).token

        match post_message_type:
            case PostMessageType.MAILING:
                username = (await Bot(custom_bot_token).get_me()).username
                text = MessageTexts.BOT_MAILINGS_MENU_ACCEPT_START.value.format(username)
            case PostMessageType.CHANNEL_POST:
                username = (await Bot(custom_bot_token).get_chat(channel_id)).username
                text = MessageTexts.BOT_CHANNEL_POST_MENU_ACCEPT_START.value.format(username)
            case PostMessageType.CONTEST:
                username = (await Bot(custom_bot_token).get_chat(channel_id)).username
                text = MessageTexts.BOT_CHANNEL_POST_MENU_ACCEPT_START.value.format(username)
            case _:
                raise UnknownPostMessageType

        await query.message.edit_text(
            text=text,
            reply_markup=InlinePostMessageStartConfirmKeyboard.get_keyboard(
                bot_id,
                post_message_id,
                post_message_type,
                channel_id=channel_id
            )
        )


async def _demo(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    post_message_id = post_message.post_message_id
    bot_id = post_message.bot_id
    media_files = await post_message_media_file_db.get_all_post_message_media_files(post_message_id)

    if await is_post_message_valid(query, post_message, post_message_type, media_files):
        custom_bot_token = (await bot_db.get_bot(bot_id)).token

        match post_message_type:
            case PostMessageType.MAILING:
                username = (await Bot(custom_bot_token).get_me()).username
            case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
                username = (await Bot(custom_bot_token).get_chat(channel_id)).username
            case _:
                raise UnknownPostMessageType

        await send_post_message(
            bot,
            query.from_user.id,
            post_message,
            media_files,
            PostActionType.DEMO,
            message=query.message
        )
        await query.message.answer(
            text=MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
            reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                bot_id, post_message_type, channel_id
            )
        )


async def _delete_post_message(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    custom_bot_token = (await bot_db.get_bot(post_message.bot_id)).token

    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
            text = MessageTexts.BOT_MAILINGS_MENU_ACCEPT_DELETING_MESSAGE.value.format(username)
        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
            text = MessageTexts.BOT_CHANNEL_POST_MENU_ACCEPT_DELETING_MESSAGE.value.format(username)
        case _:
            raise UnknownPostMessageType

    await query.message.edit_text(
        text=text,
        reply_markup=await InlinePostMessageAcceptDeletingKeyboard.get_keyboard(
            post_message.bot_id,
            post_message.post_message_id,
            post_message_type,
            channel_id
        )
    )


async def _extra_settings(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    await query.message.edit_text(
        text=query.message.html_text + "\n\n🔎 Что такое <a href=\"https://www.google.com/url?sa=i&url=https%3A"
                                       "%2F%2Ftlgrm.ru%2Fblog%2Flink-preview.html&psig=AOvVaw27FhHb7fFrLDNGUX-u"
                                       "zG7y&ust=1717771529744000&source=images&cd=vfe&opi=89978449&ved=0CBIQjR"
                                       "xqFwoTCJj5puKbx4YDFQAAAAAdAAAAABAE\">предпросмотр ссылок</a>",
        reply_markup=InlinePostMessageExtraSettingsKeyboard.get_keyboard(
            post_message.bot_id,
            post_message.post_message_id,
            post_message.enable_notification_sound,
            post_message.enable_link_preview,
            post_message_type,
            channel_id
        ),
        parse_mode=ParseMode.HTML,
    )


async def _delay(
        query: CallbackQuery,
        state: FSMContext,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    await query.message.answer(
        MessageTexts.show_date_rules(name="начала отправки сообщения"),
        reply_markup=ReplyBackPostMessageMenuKeyboard.get_keyboard()
    )
    await query.answer()
    await state.set_state(States.EDITING_POST_DELAY_DATE)
    await state.set_data({
        "bot_id": post_message.bot_id,
        "channel_id": channel_id,
        "post_message_id": post_message.post_message_id,
        "post_message_type": post_message_type.value
    })


async def _remove_delay(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    post_message.is_delayed = False
    post_message.send_date = None

    await post_message_db.update_post_message(post_message)

    await query.message.edit_reply_markup(
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            post_message.bot_id, post_message_type, channel_id
        )
    )


async def _back(
        query: CallbackQuery,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType,
        channel_id: int | None
):
    bot_id = post_message.bot_id
    custom_bot_username = (await Bot(query.bot.token).get_me()).username

    match post_message_type:
        case PostMessageType.MAILING:
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(bot_id),
                parse_mode=ParseMode.HTML
            )
        case PostMessageType.CHANNEL_POST | PostMessageType.CONTEST:
            custom_bot = await bot_db.get_bot(bot_id)

            username = (await Bot(custom_bot.token).get_chat(channel_id)).username
            await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(username, custom_bot_username),
                reply_markup=await InlineChannelMenuKeyboard.get_keyboard(bot_id, channel_id),
                parse_mode=ParseMode.HTML
            )
        case _:
            raise UnknownPostMessageType


async def _post_message_mailing(
        query: CallbackQuery,
        callback_data: InlinePostMessageMenuKeyboard.Callback,
        bot_id: int,
        post_message: PostMessageSchema,
):
    match callback_data.a:
        # RUNNING ACTIONS
        case callback_data.ActionEnum.STATISTICS:
            custom_users_length = len(await custom_bot_user_db.get_custom_bot_users(bot_id=bot_id))

            await query.answer(
                text=MessageTexts.show_mailing_info(
                    sent_post_message_amount=post_message.sent_post_message_amount,
                    custom_bot_users_len=custom_users_length,
                ),
                show_alert=True
            )


async def _post_message_union(
        query: CallbackQuery,
        state: FSMContext,
        callback_data: InlinePostMessageMenuKeyboard.Callback,
        user_id: int,
        post_message: PostMessageSchema,
        post_message_type: PostMessageType):
    match callback_data.a:
        # RUNNING ACTIONS
        case callback_data.ActionEnum.CANCEL:
            await _cancel_send(
                query,
                post_message,
                post_message_type,
                user_id,
                channel_id=get_channel_id(callback_data, post_message_type)
            )
        case callback_data.ActionEnum.STATISTICS:
            match post_message_type:
                case PostMessageType.CONTEST:
                    contest = await contest_db.get_contest_by_post_message_id(post_message.post_message_id)
                    contest_users = await contest_db.get_contest_users(contest.contest_id)
                    if contest_users:
                        path = await generate_contest_users_graph(contest.contest_id)
                        await query.message.answer_photo(FSInputFile(path),
                                                         caption="📈 График количества участников конкурса от времени.")
                        await query.answer()
                    else:
                        await query.answer("В конкурсе никто ещё не принял участие")

        # NOT RUNNING ACTIONS
        case callback_data.ActionEnum.BUTTON_ADD:
            await _button_add(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.BUTTON_URL:
            await _button_url(
                query,
                state,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.BUTTON_TEXT:
            await _button_text(
                query,
                state,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.BUTTON_DELETE:
            await _button_delete(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.POST_MESSAGE_TEXT:
            await _post_message_text(
                query,
                state,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.POST_MESSAGE_MEDIA:
            await _post_message_media(
                query,
                state,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.START:
            await _start(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.DEMO:
            await _demo(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.DELETE_POST_MESSAGE:
            await _delete_post_message(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.EXTRA_SETTINGS:
            await _extra_settings(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.DELAY:
            await _delay(
                query,
                state,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.REMOVE_DELAY:
            await _remove_delay(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.BACK:
            await _back(
                query,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        # CONTEST ACTIONS
        case callback_data.ActionEnum.WINNERS_COUNT:
            await _contest_winners_count(
                query,
                state,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.CONTEST_FINISH_DATE:
            await _contest_finish_date(
                query,
                state,
                post_message,
                post_message_type,
                channel_id=get_channel_id(callback_data, post_message_type)
            )

        case callback_data.ActionEnum.PRE_FINISH:
            await _cancel_send(
                query,
                post_message,
                post_message_type,
                user_id,
                channel_id=callback_data.channel_id,
                contest_pre_finish=True
            )


async def post_message_handler(
        query: CallbackQuery,
        state: FSMContext,
        callback_data: InlinePostMessageMenuKeyboard.Callback,
        post_message: PostMessageSchema
):
    post_message_type = callback_data.post_message_type
    user_id = query.from_user.id
    bot_id = post_message.bot_id

    match post_message_type:
        case PostMessageType.MAILING:  # specific buttons for mailing
            await _post_message_mailing(
                query, callback_data, bot_id, post_message
            )
        case PostMessageType.CHANNEL_POST:  # specific buttons for channel post
            pass

    # union buttons for mailing and channel post
    await _post_message_union(
        query,
        state,
        callback_data,
        user_id,
        post_message,
        post_message_type
    )


async def _inline_no_button(
        query: CallbackQuery,
        bot_id: int,
        post_message_type: PostMessageType,
        channel_id: int | None
) -> None:
    custom_bot_token = (await bot_db.get_bot(bot_id)).token

    match post_message_type:
        case PostMessageType.MAILING:
            username = (await Bot(custom_bot_token).get_me()).username
            text = "В этом рассылочном сообщении кнопки нет"
        case PostMessageType.CHANNEL_POST:
            username = (await Bot(custom_bot_token).get_chat(channel_id)).username
            text = "В этой записи для канала кнопки нет"
        case PostMessageType.CONTEST:
            raise ContestMessageDontNeedButton
        case _:
            raise UnknownPostMessageType

    await query.answer(
        text, show_alert=True
    )
    await query.message.edit_text(
        text=MessageTexts.bot_post_message_menu_message(post_message_type).format(username),
        reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
            bot_id, post_message_type, channel_id
        ),
        parse_mode=ParseMode.HTML
    )
