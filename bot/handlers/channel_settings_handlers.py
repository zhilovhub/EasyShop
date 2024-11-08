from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery

from common_utils.keyboards.keyboards import InlineBotMenuKeyboard

from bot.utils import MessageTexts
from bot.handlers.routers import channel_menu_router
from bot.keyboards.channel_keyboards import (
    InlineChannelsListKeyboard,
    InlineChannelMenuKeyboard,
    InlineContestTypeKeyboard,
)
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard
from bot.post_message.post_message_create import post_message_create

from database.config import bot_db, channel_user_db, channel_post_db, contest_db, post_message_db
from database.models.contest_model import ContestNotFoundError
from database.models.channel_post_model import ChannelPostNotFoundError
from database.models.post_message_model import PostMessageType

from logs.config import logger, extra_params


@channel_menu_router.callback_query(lambda query: InlineChannelsListKeyboard.callback_validator(query.data))
async def channels_list_callback_handler(query: CallbackQuery):
    """Срабатывает, когда пользователь просматривает список каналов"""

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
                    channel_username, (await custom_tg_bot.get_me()).username
                ),
                reply_markup=await InlineChannelMenuKeyboard.get_keyboard(custom_bot.bot_id, channel_id),
            )
        case callback_data.ActionEnum.BACK_TO_MAIN_MENU:
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, query.from_user.id),
                parse_mode=ParseMode.HTML,
            )


@channel_menu_router.callback_query(lambda query: InlineChannelMenuKeyboard.callback_validator(query.data))
async def channel_menu_callback_handler(query: CallbackQuery):
    """Когда пользователь находится в меню управления каналом"""

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
                show_alert=True,
            )
        case callback_data.ActionEnum.LEAVE_CHANNEL:
            leave_result = await custom_tg_bot.leave_chat(chat_id=channel_id)

            if leave_result:
                await query.message.answer(f"Вышел из канала @{channel_username}")
            else:
                await query.message.answer(f"Произошла ошибка при выходе из канала @{channel_username}")
            await query.message.edit_text(
                MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlineChannelsListKeyboard.get_keyboard(custom_bot.bot_id),
            )
        case callback_data.ActionEnum.CREATE_POST_MESSAGE | callback_data.ActionEnum.EDIT_POST_MESSAGE:
            try:
                channel_post = await channel_post_db.get_channel_post_by_bot_id(bot_id=bot_id)
                if callback_data.a == callback_data.ActionEnum.CREATE_POST_MESSAGE:
                    await query.answer("Запись уже создана", show_alert=True)
            except ChannelPostNotFoundError:
                channel_post = None

            if not channel_post and callback_data.a == callback_data.ActionEnum.CREATE_POST_MESSAGE:
                await post_message_create(bot_id, PostMessageType.CHANNEL_POST)

            await query.message.edit_text(
                MessageTexts.bot_post_message_menu_message(PostMessageType.CHANNEL_POST).format(channel_username),
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                    bot_id=bot_id, post_message_type=PostMessageType.CHANNEL_POST, channel_id=channel_id
                ),
            )
        case callback_data.ActionEnum.BACK_CHANNELS_LIST:
            await query.message.edit_text(
                text=MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format(custom_bot_username),
                reply_markup=await InlineChannelsListKeyboard.get_keyboard(bot_id),
            )
        case callback_data.ActionEnum.CREATE_CONTEST | callback_data.ActionEnum.EDIT_CONTEST:
            try:
                contest = await contest_db.get_contest_by_bot_id(bot_id=bot_id)

                if callback_data.a == callback_data.ActionEnum.CREATE_CONTEST:
                    await query.answer("В канале уже есть активный конкурс", show_alert=True)

                post_message = await post_message_db.get_post_message(contest.post_message_id)
                if post_message.is_running:
                    message_text = MessageTexts.BOT_CHANNEL_CONTEST_MENU_WHILE_RUNNING.value.format(channel_username)
                else:
                    message_text = MessageTexts.bot_post_message_menu_message(PostMessageType.CONTEST).format(
                        channel_username
                    )

                await query.message.edit_text(
                    message_text,
                    reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                        bot_id=bot_id, post_message_type=PostMessageType.CONTEST, channel_id=channel_id
                    ),
                )
                return
            except ContestNotFoundError:
                if callback_data.a == callback_data.ActionEnum.CREATE_CONTEST:
                    return await query.message.edit_text(
                        MessageTexts.SELECT_CONTEST_TYPE.value,
                        reply_markup=await InlineContestTypeKeyboard.get_keyboard(bot_id=bot_id, channel_id=channel_id),
                    )


@channel_menu_router.callback_query(lambda query: InlineContestTypeKeyboard.callback_validator(query.data))
async def contest_type_callback_handler(query: CallbackQuery):
    """Выбор типа конкурсной записи в канал"""

    callback_data = InlineContestTypeKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id
    channel_id = callback_data.channel_id

    custom_bot = await bot_db.get_bot(bot_id)
    custom_tg_bot = Bot(custom_bot.token)

    channel_username = (await custom_tg_bot.get_chat(channel_id)).username

    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_CHANNEL_MENU:
            await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(
                    channel_username, (await custom_tg_bot.get_me()).username
                ),
                reply_markup=await InlineChannelMenuKeyboard.get_keyboard(custom_bot.bot_id, channel_id),
            )
        case callback_data.ActionEnum.RANDOMIZER:
            try:
                await contest_db.get_contest_by_bot_id(bot_id=bot_id)
                return await query.answer("В канале уже есть активный конкурс", show_alert=True)
            except ContestNotFoundError:
                await post_message_create(bot_id, PostMessageType.CONTEST, contest_winners_count=1)

            await query.message.edit_text(
                MessageTexts.bot_post_message_menu_message(PostMessageType.CONTEST).format(channel_username),
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                    bot_id=bot_id, post_message_type=PostMessageType.CONTEST, channel_id=channel_id
                ),
            )
        case _:
            logger.warning(
                "Unknown callback in contest type select kb", extra_params(bot_id=bot_id, user_id=query.from_user.id)
            )
