from datetime import timedelta
import re
from datetime import datetime

from aiogram.enums import ParseMode

from aiogram.types import Message, CallbackQuery, LinkPreviewOptions, \
    InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument, BufferedInputFile
from aiogram.fsm.context import FSMContext

from database.models.contest_channel_model import ContestChannelSchema, ContestChannelSchemaWithoutId
from bot.main import bot, _scheduler, custom_bot_user_db, channel_post_media_file_db, channel_user_db, contest_channel_db, contest_user_db
from bot.states.states import States
from bot.handlers.routers import channel_menu_router

from logs.config import logger


from database.models.bot_model import BotSchema
from database.models.channel_post_model import ChannelPostSchemaWithoutId, ContestTypeValues
from database.models.channel_post_media_files_model import ChannelPostMediaFileSchema
from aiogram.utils.deep_linking import create_start_link
from bot.keyboards import *
from utils.contest_result import generate_contest_result


class MailingMessageType(Enum):
    DEMO = "demo"  # Демо сообщение с главного бота
    # Демо сообщение с главного бота (но немного другой функионал для отправки)
    AFTER_REDACTING = "after_redacting"
    # Главная рассылка (отправка с кастомного бота всем пользователям)
    RELEASE = "release"


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

    # Channel specific actions (can be executed without additional validation)
    match action:
        case "analytics":
            plus_users = await channel_user_db.get_joined_channel_users_by_channel_id(channel_id)
            minus_users = await channel_user_db.get_left_channel_users_by_channel_id(channel_id)
            return await query.answer(
                text=f"Прирост подписчиков в канале @{channel_username}: {len(plus_users)-len(minus_users)}\n\n"
                f"Отписалось - {len(minus_users)}\n"
                f"Подписалось - {len(plus_users)}\n",
                show_alert=True
            )
        case "leave_channel":
            leave_result = await custom_tg_bot.leave_chat(chat_id=channel_id)
            if leave_result:
                await query.message.answer(f"Вышел из канала {channel_username}.")
                await query.message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await get_inline_bot_menu_keyboard(bot_id)
                )
            else:
                await query.message.answer(f"Произошла ошибка при выходе из канала {channel_username}")
                await query.message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await get_inline_bot_menu_keyboard(bot_id)
                )
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
                    reply_markup=await get_inline_bot_menu_keyboard(bot_id)
                )
                return await query.message.delete()
            case _:
                if channel_post.is_contest:
                    await query.answer("Сейчас в канале есть активный конкурс, дождитесь когда он закончится", show_alert=True)
                else:
                    await query.answer("Пост уже в очереди", show_alert=True)
                await query.message.answer(
                    text=MessageTexts.BOT_CHANNEL_POST_MENU_WHILE_RUNNING.value.format(
                        channel_username),
                    reply_markup=await get_inline_bot_channel_post_menu_keyboard(
                        bot_id, channel_id, is_contest=channel_post.is_contest)
                )
                return await query.message.delete()

    # If channel_post is still None, it means that the requested objectd is deleted or
    # not created yet, which means we receive "create_post" or "create_contest" request
    # other requests will be blocked
    if channel_post is None:
        match action:
            case "create_post":
                try:
                    await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=False)
                    await query.answer(
                        "Пост для этого канала уже создан",
                        show_alert=True
                    )
                    await query.message.delete()
                    return await query.message.edit_text(
                        MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                            channel_username),
                        reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id)
                    )
                except ChannelPostNotFound:
                    pass
                await channel_post_db.add_channel_post(ChannelPostSchemaWithoutId.model_validate(
                    {"channel_id": channel_id, "bot_id": bot_id,
                        "created_at": datetime.now().replace(tzinfo=None), "contest_type": ContestTypeValues.NONE}
                ))
                custom_bot = await bot_db.get_bot(bot_id=bot_id)
                return await query.message.answer(
                    MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                        channel_username),
                    reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id)
                )
            case "create_contest":  # TODO Change to contest
                try:
                    await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=True)
                    await query.answer(
                        "Конкурс для этого канала уже создан",
                        show_alert=True
                    )
                    await query.message.delete()
                    return await query.message.edit_text(
                        MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                            channel_username),
                        reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=True)
                    )
                except ChannelPostNotFound:
                    pass
                await channel_post_db.add_channel_post(ChannelPostSchemaWithoutId.model_validate(
                    {"channel_id": channel_id, "bot_id": bot_id,
                        "created_at": datetime.now().replace(tzinfo=None), "is_contest": True,
                        "contest_type": ContestTypeValues.RANDOM,
                        "has_button": True,
                        "button_text": "Участвовать (0)"
                     }
                ))
                custom_bot = await bot_db.get_bot(bot_id=bot_id)
                return await query.message.answer(
                    MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                        channel_username),
                    reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=True)
                )
            case _:
                await query.answer("Запись не найдена", show_alert=True)
                try:
                    await query.message.delete()
                except:
                    pass

    # Works only if we get requested object from db
    match action:
        case "get_sponsors":  # TODO Add instruction on how to create chat folder links

            if channel_post.contest_sponsor_url:
                await query.message.answer(
                    f"Отправьте ссылку на новую папку\n\n"
                    f"Текущая - {channel_post.contest_sponsor_url}",
                    reply_markup=get_back_keyboard()
                )
            else:
                await query.message.answer(
                    f"Отправьте ссылку на папку с каналами спонсоров\n\n",
                    reply_markup=get_back_keyboard()
                )
            await query.answer()
            await state.set_state(States.EDITING_SPONSOR_LINK)
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
        case "get_contest_button_text":
            await query.message.answer(
                f"Введите текст, который будет отображаться на кнопке\n\n"
                "Справа будет отображаться счетчик участвующих",
                reply_markup=get_back_keyboard()
            )
            await query.answer()
            await state.set_state(States.EDITING_POST_BUTTON_TEXT)
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
        case "get_contest_winner_amount":
            await query.message.answer(f"Введите количество победителей в конкурсе", reply_markup=get_back_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_COMPETITION_WINNER_AMOUNT)
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
        case "pick_contest_type":
            if channel_post.contest_type == ContestTypeValues.RANDOM:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
            else:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
            await query.message.answer(
                text=menu_text,
                reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
            )
            # await query.message.answer(
            #     text=f"Текущий тип конкурса - {channel_post.contest_type.value}\n"
            #     f"Выберите нужный тип конкурса: ",
            #     reply_markup=await get_contest_type_pick_keyboard(bot_id, channel_id)
            # )
        case "pick_random_contest":
            try:
                await query.message.delete()
            except:
                pass
            if channel_post.contest_type != ContestTypeValues.RANDOM:
                channel_post.contest_type = ContestTypeValues.RANDOM
                await channel_post_db.update_channel_post(channel_post)
            await query.message.answer("Текущий тип конкурса - Рандомайзер")
            await state.set_state(States.BOT_MENU)
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
            # return await query.message.answer(
            #     MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
            #         channel_username),
            #     reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
            # )
            if channel_post.contest_type == ContestTypeValues.RANDOM:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
            else:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
            await query.message.answer(
                text=menu_text,
                reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
            )

        case "pick_sponsor_contest":
            try:
                await query.message.delete()
            except:
                pass
            if channel_post.contest_type != ContestTypeValues.SPONSOR:
                channel_post.contest_type = ContestTypeValues.SPONSOR
                await channel_post_db.update_channel_post(channel_post)
            await query.message.answer("Текущий тип конкурса - Спонсорство\n\n Настройте спонсоров с помощью появившейся кнопки")
            await state.set_state(States.BOT_MENU)
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
            # return await query.message.answer(
            #     MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
            #         channel_username),
            #     reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
            # )
            if channel_post.contest_type == ContestTypeValues.RANDOM:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
            else:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
            await query.message.answer(
                text=menu_text,
                reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
            )
        case "get_contest_end_date":
            await query.message.answer(f"Введите дату окончания конкурса\n\n{MessageTexts.DATE_RULES.value}",
                                       reply_markup=get_back_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_COMPETITION_END_DATE)
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
        case "cancel_delay":
            channel_post.is_delayed = False
            channel_post.send_date = None
            await channel_post_db.update_channel_post(channel_post)
            await query.message.edit_reply_markup(reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id, channel_id, channel_post.is_contest))
        case "edit_post":
            if channel_post.is_contest:
                if channel_post.is_running is True and channel_post.is_delayed is False:
                    return await query.answer("Сейчас уже идет конкурс, дождитесь его завершения")
            return await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                    channel_username),
                reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
            )
        case "message":

            await query.message.answer("Введите текст, который будет отображаться в посте",
                                       reply_markup=get_back_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_POST_TEXT)
            if channel_post.is_contest:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
            else:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id})
        case "back_to_channels_list":
            await query.message.edit_text(
                text=MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format(
                    custom_bot_username),
                reply_markup=await get_inline_bot_channels_list_keyboard(bot_id)
            )
        case "back_to_channel_list":
            await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(channel_username, (await custom_tg_bot.get_me()).username),
                reply_markup=await get_inline_channel_menu_keyboard(custom_bot.bot_id, channel_id)
            )
        case "demo":
            media_files = await channel_post_media_file_db.get_all_channel_post_media_files(channel_post_id=channel_post.channel_post_id)

            if len(media_files) > 1 and channel_post.has_button:
                await query.answer(
                    "Telegram не позволяет прикрепить кнопку, если в сообщении минимум 2 медиафайла",
                    show_alert=True
                )
            elif channel_post.description or media_files:
                media_files = await channel_post_media_file_db.get_all_channel_post_media_files(channel_post_id=channel_post.channel_post_id)
                await send_channel_post_message(
                    bot,
                    query.from_user.id,
                    channel_post,
                    media_files,
                    MailingMessageType.DEMO,
                    query.from_user.id,
                    query.message.message_id
                )
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                        custom_bot_username
                    ),
                    reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id, channel_id, is_contest=channel_post.is_contest)
                )

            else:
                await query.answer(
                    text="В Вашем рассылочном сообщении нет ни текста, ни медиафайлов",
                    show_alert=True
                )
        case "media":
            await query.message.answer("Отправьте одним сообщением медиафайлы для поста\n\n"
                                       "❗ Старые медиафайлы к этому посту <b>перезапишутся</b>\n\n"
                                       "❗❗ Обратите внимание, что к сообщению нельзя будет прикрепить кнопку, если медиафайлов <b>больше одного</b>",
                                       reply_markup=get_confirm_media_upload_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_POST_MEDIA_FILES)
            if channel_post.is_contest:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
            else:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id})
        case "button_url":
            if not channel_post.has_button:
                await query.answer("В посте кнопки уже нет", show_alert=True)
                await query.message.delete()
            else:
                await query.message.answer("Введите ссылку, которая будет открываться по нажатию на кнопку",
                                           reply_markup=get_back_keyboard())
                await query.answer()
                await state.set_state(States.EDITING_POST_BUTTON_URL)
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id})
        case "button_text":
            if not channel_post.has_button:
                await query.answer("В посте кнопки уже нет", show_alert=True)
                await query.message.delete()
            else:
                await query.message.answer("Введите текст, который будет отображаться на кнопке",
                                           reply_markup=get_back_keyboard())
                await query.answer()
                await state.set_state(States.EDITING_POST_BUTTON_TEXT)
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id})
        case "delete_button":
            if not channel_post.has_button:
                await query.answer("В посте кнопки уже нет", show_alert=True)
                await query.message.delete()
            else:
                channel_post.button_text = None
                channel_post.button_url = None
                channel_post.has_button = False
                await channel_post_db.update_channel_post(channel_post)

                await query.message.answer("Кнопка удалена\n\n")
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                        custom_bot_username
                    ),
                    reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id, channel_id, channel_post.is_contest)
                )
        case "add_button":
            media_files = await channel_post_media_file_db.get_all_channel_post_media_files(channel_post_id=channel_post.channel_post_id)

            if channel_post.has_button:
                await query.answer("В посте кнопка уже есть", show_alert=True)
                await query.message.delete()
            elif len(media_files) > 1:
                await query.answer("Кнопку нельзя добавить, если в сообщение больше одного медиафайла", show_alert=True)
            else:
                channel_post.button_text = "Shop"
                link = await create_start_link(custom_tg_bot, 'show_shop_inline')
                # channel_post.button_url = f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id={bot_id}"
                channel_post.button_url = link
                channel_post.has_button = True
                await channel_post_db.update_channel_post(channel_post)

                await query.message.answer("Кнопка добавлена\n\n"
                                           "Сейчас там стандартный текст 'Магазин' и ссылка на Ваш магазин.\n"
                                           "Эти два параметры Вы можете изменить в настройках рассылки")
                await query.message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                        custom_bot_username
                    ),
                    reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id, channel_id, channel_post.is_Contest)
                )
        # TODO Add contest validation
        case "start":
            media_files = await channel_post_media_file_db.get_all_channel_post_media_files(channel_post_id=channel_post.channel_post_id)

            if len(media_files) > 1 and channel_post.has_button:
                return await query.answer(
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
                elif channel_post.contest_type == ContestTypeValues.SPONSOR and channel_post.contest_sponsor_url is None:
                    return await query.answer(
                        text="Не выбраны каналы спонсоры",
                        show_alert=True
                    )
                elif channel_post.contest_end_date < (timedelta(minutes=2) + datetime.now()):
                    return await query.answer(
                        text="Дата окончания конкурса уже прошла",
                        show_alert=True
                    )
            await query.message.edit_text(
                text=MessageTexts.BOT_CHANNEL_POST_MENU_ACCEPT_START.value.format(
                    channel_username),
                reply_markup=await get_inline_bot_channel_post_start_confirm_keybaord(bot_id, channel_id, channel_post.is_contest)
            )
        case "accept_start":
            media_files = await channel_post_media_file_db.get_all_channel_post_media_files(channel_post_id=channel_post.channel_post_id)

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
                elif channel_post.contest_type == ContestTypeValues.SPONSOR and channel_post.contest_sponsor_url is None:
                    return await query.answer(
                        text="Не выбраны каналы спонсоры",
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
                    await send_channel_post_message(
                        bot_from_send=custom_bot,
                        to_user_id=channel_post.channel_id,
                        channel_post_schema=channel_post,
                        media_files=media_files,
                        mailing_message_type=MailingMessageType.RELEASE,
                        chat_id=query.from_user.id,
                        message_id=query.message.message_id,
                    )
                    await query.message.edit_text(
                        MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(channel_username, (await custom_tg_bot.get_me()).username),
                        reply_markup=await get_inline_channel_menu_keyboard(custom_bot.bot_id, channel_id)
                    )
                else:
                    job_id = await _scheduler.add_scheduled_job(
                        func=send_channel_post_message, run_date=channel_post.send_date, args=[custom_bot, channel_post.channel_id, channel_post, media_files, MailingMessageType.RELEASE, query.from_user.id, query.message.message_id])
                    channel_post.job_id = job_id
                    await channel_post_db.update_channel_post(channel_post)
            else:
                await query.answer(
                    text="В Вашем рассылочном сообщении нет ни текста, ни медиафайлов",
                    show_alert=True
                )
        case "extra_settings":
            await query.message.edit_text(
                text=query.message.html_text + "\n\n🔎 Что такое <a href=\"https://www.google.com/url?sa=i&url=https%3A%2F%2Ftlgrm.ru%2Fblog%2Flink-preview.html&psig=AOvVaw27FhHb7fFrLDNGUX-uzG7y&ust=1717771529744000&source=images&cd=vfe&opi=89978449&ved=0CBIQjRxqFwoTCJj5puKbx4YDFQAAAAAdAAAAABAE\">предпросмотр ссылок</a>",
                parse_mode=ParseMode.HTML,
                reply_markup=await get_inline_bot_channel_post_menu_extra_settings_keyboard(
                    bot_id,
                    channel_id,
                    channel_post.enable_notification_sound,
                    channel_post.enable_link_preview,
                    channel_post.is_contest
                )
            )
        case "toggle_link_preview":
            channel_post.enable_link_preview = False if channel_post.enable_link_preview else True
            await channel_post_db.update_channel_post(channel_post)
            await query.message.edit_reply_markup(
                reply_markup=await get_inline_bot_channel_post_menu_extra_settings_keyboard(
                    bot_id,
                    channel_id,
                    channel_post.enable_notification_sound,
                    channel_post.enable_link_preview,
                    channel_post.is_contest
                )
            )
        case "toggle_notigication_sound":
            channel_post.enable_notification_sound = False if channel_post.enable_notification_sound else True
            await channel_post_db.update_channel_post(channel_post)
            await query.message.edit_reply_markup(
                reply_markup=await get_inline_bot_channel_post_menu_extra_settings_keyboard(
                    bot_id,
                    channel_id,
                    channel_post.enable_notification_sound,
                    channel_post.enable_link_preview,
                    channel_post.is_contest
                )
            )
        case "back_to_editing_channel_post":
            return await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                    channel_username),
                reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
            )

        case "delete_channel_post":
            await query.message.edit_text(
                text=MessageTexts.BOT_CHANNEL_POST_MENU_ACCEPT_DELETING_MESSAGE.value.format(
                    channel_username),
                reply_markup=await get_inline_bot_channel_post_menu_accept_deleting_keyboard(bot_id, channel_id, channel_post.is_contest)
            )

        case "accept_delete":
            await channel_post_db.delete_channel_post(channel_post_id=channel_post.channel_post_id)
            await query.answer(
                text="Пост удален",
                show_alert=True
            )
            await query.message.answer(
                text=MessageTexts.BOT_MENU_MESSAGE.value.format(
                    custom_bot_username),
                reply_markup=await get_inline_bot_menu_keyboard(
                    bot_id)
            )
            await query.message.delete()
        case "delay":
            await query.message.answer(f"Введите дату рассылки\n\n{MessageTexts.DATE_RULES.value}",
                                       reply_markup=get_back_keyboard())
            await query.answer()
            await state.set_state(States.EDITING_POST_DELAY_DATE)
            if channel_post.is_contest:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
            else:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id})


@channel_menu_router.message(States.EDITING_SPONSOR_LINK)
async def editing_contest_sponsor_url(message: Message, state: FSMContext):
    message_text = message.html_text
    state_data = await state.get_data()
    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]
    if state_data.get("channel_post_id", None) != None:
        is_contest_flag = True
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    channel_username = (await custom_bot_tg.get_chat(channel_id)).username
    channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=is_contest_flag)
    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            if channel_post.contest_type == ContestTypeValues.RANDOM:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
            else:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
            await message.answer(
                text=menu_text,
                reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
            )
            await state.set_state(States.BOT_MENU)
        else:
            if message_text.startswith("https://t.me/addlist/") is False:
                return await message.answer("Вы ввели не ту ссылку, попробуйте еще раз.")
            await message.answer(f"Ваши спонсоры изменены на {message_text}")
            # await message.answer(
            #     MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
            #         channel_username),
            #     reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
            # )
            await message.answer(f"Теперь введите через энтер ссылки на каналы\n\nПример:\nhttps://t.me/durov_russia\nhttps://t.me/durov_russia\nhttps://t.me/durov_russia\n")
            await state.set_state(States.WAITING_FOR_SPONSOR_CHANNEL_LINKS)
            if channel_post.is_contest:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id, "sponsor_url": message_text})
            else:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id})


@channel_menu_router.message(States.WAITING_FOR_SPONSOR_CHANNEL_LINKS)
async def editing_sponsor_channel_links(message: Message, state: FSMContext):
    message_text = message.html_text
    state_data = await state.get_data()
    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]
    if state_data.get("channel_post_id", None) != None:
        is_contest_flag = True
    sponsor_url = state_data["sponsor_url"]
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    channel_username = (await custom_bot_tg.get_chat(channel_id)).username
    channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=is_contest_flag)
    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            if channel_post.contest_type == ContestTypeValues.RANDOM:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
            else:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
            await message.answer(
                text=menu_text,
                reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
            )
            await state.set_state(States.BOT_MENU)
        else:
            ids_list = []
            links = [link.strip() for link in message_text.split("\n")]
            for link in links:
                if link.startswith("https://t.me/") is False:
                    return await message.answer("Введенная ссылка не ведет на канал")
                try:
                    s_channel = await bot.get_chat(f"@{link.split('/')[-1]}")
                except Exception as e:
                    return await message.answer("Введенная ссылка не ведет на канал 1")
                if s_channel.id:
                    ids_list.append(s_channel.id)
                else:
                    return await message.answer("Введенная ссылка не ведет на канал 2")
            await contest_channel_db.delete_channels_by_contest_id(contest_id=channel_post.channel_post_id)
            for ch_id in ids_list:
                await contest_channel_db.add_channel(
                    ContestChannelSchemaWithoutId.model_validate(
                        {"channel_id": ch_id,
                            "contest_post_id": channel_post.channel_post_id}
                    )
                )
            channel_post.contest_sponsor_url = sponsor_url
            await channel_post_db.update_channel_post(channel_post)
            await message.answer("Ваши каналы сохранены")
            if channel_post.contest_type == ContestTypeValues.RANDOM:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
            else:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
            await message.answer(
                text=menu_text,
                reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
            )
            await state.set_state(States.BOT_MENU)
            if channel_post.is_contest:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
            else:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id})


@channel_menu_router.message(States.EDITING_COMPETITION_WINNER_AMOUNT)
async def editing_competition_winner_amount(message: Message, state: FSMContext):
    message_text = message.html_text
    state_data = await state.get_data()
    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]
    if state_data.get("channel_post_id", None) != None:
        is_contest_flag = True
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    channel_username = (await custom_bot_tg.get_chat(channel_id)).username
    channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=is_contest_flag)
    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            if channel_post.contest_type == ContestTypeValues.RANDOM:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
            else:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
            await message.answer(
                text=menu_text,
                reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
            )
            await state.set_state(States.BOT_MENU)
        else:
            try:
                winner_amount = int(message_text)
                if (winner_amount < 0) or (winner_amount > 2_000_000):
                    await message.answer("Введите положительное число, меньшее 2млн")
                    return
            except ValueError:
                return await message.answer("Вы ввели не число")

            channel_post.contest_winner_amount = winner_amount
            await channel_post_db.update_channel_post(channel_post)
            await message.answer(f"Количество победителей: {winner_amount}")
            # await message.answer(
            #     MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
            #         channel_username),
            #     reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
            # )
            if channel_post.contest_type == ContestTypeValues.RANDOM:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
            else:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
            await message.answer(
                text=menu_text,
                reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
            )
            await state.set_state(States.BOT_MENU)
            if channel_post.is_contest:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
            else:
                await state.set_data({"bot_id": bot_id, "channel_id": channel_id})


@channel_menu_router.message(States.EDITING_COMPETITION_END_DATE)
async def editing_competition_end_date(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()
    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]
    if state_data.get("channel_post_id", None) != None:
        is_contest_flag = True

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    channel_username = (await custom_bot_tg.get_chat(channel_id)).username
    channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=is_contest_flag)
    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            if channel_post.contest_type == ContestTypeValues.RANDOM:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
            else:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
            await message.answer(
                text=menu_text,
                reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
            )
            await state.set_state(States.BOT_MENU)
        else:
            try:
                datetime_obj = datetime.strptime(
                    message_text, "%d.%m.%Y %H:%M")
                datetime_obj.replace(tzinfo=None)
                if datetime.now() > datetime_obj:
                    await message.reply("Введенное время уже прошло, попробуйте ввести другое")
                    return

                channel_post.contest_end_date = datetime_obj

                await channel_post_db.update_channel_post(channel_post)

                await message.reply(f"Конец конкурса: {datetime_obj.strftime('%Y-%m-%d %H:%M')}")
                # await message.answer(
                #     MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                #         channel_username),
                #     reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
                # )
                if channel_post.contest_type == ContestTypeValues.RANDOM:
                    menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                        channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
                else:
                    menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                        ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
                await message.answer(
                    text=menu_text,
                    reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
                )

                await state.set_state(States.BOT_MENU)
                if channel_post.is_contest:
                    await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
                else:
                    await state.set_data({"bot_id": bot_id, "channel_id": channel_id})
            except ValueError:
                await message.reply("Некорректный формат. Пожалуйста, введите время и дату в правильном формате.")


@channel_menu_router.message(States.EDITING_POST_DELAY_DATE)
async def editing_channel_post_delay_date_handler(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]
    is_contest_flag = False
    if state_data.get("channel_post_id", None) != None:
        is_contest_flag = True

    channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=is_contest_flag)
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username
    channel_username = (await custom_bot_tg.get_chat(channel_id)).username
    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                    channel_username),
                reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
            )
            await state.set_state(States.BOT_MENU)
        else:
            try:
                datetime_obj = datetime.strptime(
                    message_text, "%d.%m.%Y %H:%M")
                datetime_obj.replace(tzinfo=None)
                if datetime.now() > datetime_obj:
                    await message.reply("Введенное время уже прошло, попробуйте ввести другое")
                    return
                channel_post.is_delayed = True
                channel_post.send_date = datetime_obj

                await channel_post_db.update_channel_post(channel_post)

                await message.reply(f"Запланировано на: {datetime_obj.strftime('%Y-%m-%d %H:%M')}\n\n"
                                    f"Для запуска отложенной рассылки нажмите <b>Запустить</b>")
                await message.answer(
                    MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                        channel_username),
                    reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
                )

                await state.set_state(States.BOT_MENU)
                if channel_post.is_contest:
                    await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
                else:
                    await state.set_data({"bot_id": bot_id, "channel_id": channel_id})
            except ValueError:
                await message.reply("Некорректный формат. Пожалуйста, введите время и дату в правильном формате.")


@channel_menu_router.message(States.EDITING_POST_MEDIA_FILES)
async def editing_channel_post_media_files_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]
    if state_data.get("channel_post_id", None) != None:
        is_contest_flag = True
    else:
        is_contest_flag = False

    channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=is_contest_flag)

    if (message.photo or message.video or message.audio or message.document) and "first" not in state_data:
        await channel_post_media_file_db.delete_channel_post_media_files(channel_post_id=channel_post.channel_post_id)
        state_data["first"] = True

    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    if message.text == "✅ Готово":

        await message.answer(
            "Возвращаемся в меню...",
            reply_markup=get_reply_bot_menu_keyboard(
                bot_id=state_data["bot_id"]
            )
        )
        await message.answer(
            text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                custom_bot_username
            ),
            reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id, channel_id, channel_post.is_contest)
        )

        await state.set_state(States.BOT_MENU)
        if channel_post.is_contest:
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
        else:
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id})

        return
    elif message.text == "Очистить":
        await message.answer("Очищаем все файлы...")
        await channel_post_media_file_db.delete_channel_post_media_files(channel_post_id=channel_post.channel_post_id)
        await message.answer("Отправьте одним сообщением медиафайлы для поста\n\n"
                             "❗ Старые медиафайлы к этому посту<b>перезапишутся</b>\n\n"
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

    await channel_post_media_file_db.add_channel_post_media_file(ChannelPostMediaFileSchema.model_validate(
        {"channel_post_id": channel_post.channel_post_id, "file_id_main_bot": file_id,
            "file_path": file_path, "media_type": media_type}
    ))

    await message.answer(answer_text)


@channel_menu_router.message(States.EDITING_POST_TEXT)
async def editing_post_message_handler(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]
    is_contest_flag = False
    if state_data.get("channel_post_id", None) != None:
        is_contest_flag = True
    channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=is_contest_flag)
    custom_bot = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot.get_me()).username
    channel_username = (await custom_bot.get_chat(channel_id)).username
    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                    channel_username),
                reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
            )
            await state.set_state(States.BOT_MENU)
        else:
            channel_post.description = message.html_text
            media_files = await channel_post_media_file_db.get_all_channel_post_media_files(channel_post_id=channel_post.channel_post_id)

            await channel_post_db.update_channel_post(channel_post)

            await message.answer(
                "Предпросмотр поста 👇",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            await send_channel_post_message(
                bot,
                message.from_user.id,
                channel_post,
                media_files,
                MailingMessageType.AFTER_REDACTING,
                message.from_user.id,
                message.message_id,
            )
            # await message.delete()
            await message.answer(
                MessageTexts.BOT_CHANNEL_POST_MENU_MESSAGE.value.format(
                    channel_username),
                reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id=bot_id, channel_id=channel_id, is_contest=channel_post.is_contest)
            )

        await state.set_state(States.BOT_MENU)
        if channel_post.is_contest:
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
        else:
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id})
    else:
        await message.answer("Описание должно содержать текст.\n"
                             "Если есть необходимость прикрепить медиафайлы, то для этого есть пункт в меню")


async def send_channel_post_message(  # TODO that's not funny
        bot_from_send: BotSchema | Bot,
        to_user_id: int,
        channel_post_schema: ChannelPostSchema,
        media_files: list[ChannelPostMediaFileSchema],
        mailing_message_type: MailingMessageType,
        chat_id: int = None,
        message_id: int = None,
) -> None:
    if mailing_message_type == MailingMessageType.RELEASE:
        bot_from_send = Bot(bot_from_send.token)
    if channel_post_schema.has_button:
        if channel_post_schema.button_url == f"{WEB_APP_URL}:{WEB_APP_PORT}/products-page/?bot_id={channel_post_schema.bot_id}":
            button = InlineKeyboardButton(
                text=channel_post_schema.button_text,
                web_app=make_webapp_info(bot_id=channel_post_schema.bot_id)
            )
        elif channel_post_schema.is_contest:
            button = InlineKeyboardButton(
                text=channel_post_schema.button_text,
                callback_data=channel_post_schema.button_query
            )
        else:
            button = InlineKeyboardButton(
                text=channel_post_schema.button_text,
                url=channel_post_schema.button_url
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
            if channel_post_schema.description:
                media_group[0].caption = channel_post_schema.description

            uploaded_media_files.extend(await bot_from_send.send_media_group(
                chat_id=to_user_id,
                media=media_group,
                disable_notification=not (
                    channel_post_schema.enable_link_preview),
            ))
            if chat_id and message_id:
                await bot.delete_message(chat_id, message_id)
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
                caption=channel_post_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    channel_post_schema.enable_notification_sound),
            ))

            if chat_id and message_id:
                await bot.delete_message(chat_id, message_id)

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
                await channel_post_media_file_db.update_media_file(old_message)
    else:
        if channel_post_schema.description is None:
            return
        if mailing_message_type == MailingMessageType.DEMO:  # только при демо с главного бота срабатывает
            await bot.send_message(chat_id=chat_id, text=channel_post_schema.description,
                                   link_preview_options=LinkPreviewOptions(is_disabled=not (
                                       channel_post_schema.enable_link_preview)),
                                   reply_markup=keyboard,)
        elif mailing_message_type == MailingMessageType.AFTER_REDACTING:
            await bot_from_send.send_message(
                chat_id=to_user_id,
                text=channel_post_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    channel_post_schema.enable_notification_sound),
                link_preview_options=LinkPreviewOptions(is_disabled=not (
                    channel_post_schema.enable_link_preview))
            )
        else:
            await bot_from_send.send_message(
                chat_id=to_user_id,
                text=channel_post_schema.description,
                reply_markup=keyboard,
                disable_notification=not (
                    channel_post_schema.enable_notification_sound),
                link_preview_options=LinkPreviewOptions(is_disabled=not (
                    channel_post_schema.enable_link_preview))
            )
    # channel_post_schema.is_running = False
    # await channel_post_db.update_channel_post(channel_post_schema)
    if mailing_message_type == MailingMessageType.RELEASE:
        if channel_post_schema.is_contest is False:
            await channel_post_db.delete_channel_post(channel_post_id=channel_post_schema.channel_post_id)
        await bot.send_message(chat_id, "Пост отправлен в канал!")
        # Scheduling contest result function
        if channel_post_schema.is_contest:
            job_id = await _scheduler.add_scheduled_job(
                func=generate_contest_result, run_date=channel_post_schema.contest_end_date, args=[channel_post_schema.channel_id])
            # await generate_contest_result(channel_post_schema.channel_id)


@channel_menu_router.message(States.EDITING_POST_BUTTON_TEXT)
async def editing_channel_post_button_text_handler(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]
    if state_data.get("channel_post_id", None) != None:
        is_contest_flag = True

    channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=is_contest_flag)
    custom_bot_tg = Bot((await bot_db.get_bot(bot_id)).token)
    custom_bot_username = (await custom_bot_tg.get_me()).username

    if message_text:
        if message_text == "🔙 Назад":
            await message.answer(
                "Возвращаемся в меню...",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            if channel_post.contest_type == ContestTypeValues.RANDOM:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
            else:
                menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                    ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
            await message.answer(
                text=menu_text,
                reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
            )
            await state.set_state(States.BOT_MENU)
        else:
            message_text = message.text
            if channel_post.is_contest:
                message_text += " (0)"
            channel_post.button_text = message_text
            media_files = await channel_post_media_file_db.get_all_channel_post_media_files(channel_post_id=channel_post.channel_post_id)
            await channel_post_db.update_channel_post(channel_post)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            await send_channel_post_message(
                bot,
                message.from_user.id,
                channel_post,
                media_files,
                MailingMessageType.AFTER_REDACTING,
                message.from_user.id,
                message.message_id,
            )
            if channel_post.is_contest is False:
                await message.answer(
                    text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                        custom_bot_username
                    ),
                    reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id, channel_id, channel_post.is_contest)
                )
            else:
                if channel_post.contest_type == ContestTypeValues.RANDOM:
                    menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                        channel_post.contest_type.value, ContestTypeValues.SPONSOR.value)
                else:
                    menu_text = MessageTexts.BOT_CONTEST_MENU.value.format(
                        ContestTypeValues.SPONSOR.value, channel_post.contest_type.value)
                await message.answer(
                    text=menu_text,
                    reply_markup=await get_contest_menu_keyboard(bot_id, channel_id, is_contest=True)
                )

        await state.set_state(States.BOT_MENU)
        if channel_post.is_contest:
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id, "channel_post_id": channel_post.channel_post_id})
        else:
            await state.set_data({"bot_id": bot_id, "channel_id": channel_id})
    else:
        await message.answer("Название кнопки должно содержать текст")


@channel_menu_router.message(States.EDITING_POST_BUTTON_URL)
async def editing_channel_post_button_url_handler(message: Message, state: FSMContext):
    message_text = message.html_text

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    channel_id = state_data["channel_id"]

    channel_post = await channel_post_db.get_channel_post(channel_id=channel_id, is_contest=False)
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
                reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id, channel_id, channel_post.is_contest)
            )
            await state.set_state(States.BOT_MENU)
        else:
            pattern = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
            if not re.fullmatch(pattern, message.text):
                return await message.answer("Невалидная ссылка. Введите, пожалуйста, ссылку в стандартном формате, начинающимся с <b>http</b> или <b>https</b>")

            channel_post.button_url = message.text
            media_files = await channel_post_media_file_db.get_all_channel_post_media_files(channel_post_id=channel_post.channel_post_id)
            await channel_post_db.update_channel_post(channel_post)

            await message.answer(
                "Предпросмотр конкурса 👇",
                reply_markup=get_reply_bot_menu_keyboard(
                    bot_id=state_data["bot_id"])
            )
            await send_channel_post_message(
                bot,
                message.from_user.id,
                channel_post,
                media_files,
                MailingMessageType.AFTER_REDACTING,
                message.from_user.id,
                message.message_id,
            )
            await message.answer(
                text=MessageTexts.BOT_MAILINGS_MENU_MESSAGE.value.format(
                    custom_bot_username
                ),
                reply_markup=await get_inline_bot_channel_post_menu_keyboard(bot_id, channel_id, channel_post.is_contest)
            )

        await state.set_state(States.BOT_MENU)
        await state.set_data({"bot_id": bot_id, "channel_id": channel_id})
    else:
        await message.answer("Ссылка должно содержать только текст")
