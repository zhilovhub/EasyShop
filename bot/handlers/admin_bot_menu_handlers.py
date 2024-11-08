import string
from random import sample
from aiohttp import ClientConnectorError

from sqlalchemy.exc import IntegrityError

from aiogram import F, Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.utils.token import validate_token, TokenValidationError
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.formatting import Text, Bold, Italic

from bot.main import bot, QUESTION_MESSAGES, cache_resources_file_id_store
from bot.utils import MessageTexts
from bot.states.states import States
from bot.handlers.routers import admin_bot_menu_router
from bot.utils.product_utils import generate_article
from bot.utils.custom_bot_api import start_custom_bot, stop_custom_bot
from bot.utils.send_instructions import greetings_message
from bot.keyboards.channel_keyboards import (
    InlineChannelPublishAcceptKeyboard,
    InlineChannelsListKeyboard,
    InlineChannelsListPublishKeyboard,
)
from bot.keyboards.main_menu_keyboards import (
    InlineAcceptPublishProductKeyboard,
    InlineBackFromRefKeyboard,
    ReplyBotMenuKeyboard,
    ReplyBackBotMenuKeyboard,
    InlineSelectLanguageKb,
)
from bot.keyboards.stock_menu_keyboards import InlineStockMenuKeyboard, InlineWebStockKeyboard
from bot.keyboards.post_message_keyboards import InlinePostMessageMenuKeyboard
from bot.post_message.post_message_create import post_message_create

from common_utils import generate_admin_invite_link
from common_utils.config import common_settings
from common_utils.bot_utils import create_bot_options, create_custom_bot
from common_utils.message_texts import MessageTexts as CommonMessageTexts
from common_utils.bot_settings_config import BOT_PROPERTIES
from common_utils.keyboards.keyboards import (
    InlineBotEditOrderOptionsKeyboard,
    InlineBotMenuKeyboard,
    InlineBotSettingsMenuKeyboard,
    InlineAdministratorsManageKeyboard,
    InlineThemeSettingsMenuKeyboard,
    InlineModeProductKeyboardButton,
    InlinePaymentSettingsKeyboard,
    InlineBotMainWebAppButton,
)
from common_utils.broadcasting.broadcasting import send_event, EventTypes
from common_utils.ref_utils import send_ref_user_info
from common_utils.storage.custom_bot_storage import custom_bot_storage
from common_utils.keyboards.order_manage_keyboards import (
    InlineOrderCancelKeyboard,
    InlineOrderStatusesKeyboard,
    InlineAcceptReviewKeyboard,
    InlineOrderCustomBotKeyboard,
    InlineCreateReviewKeyboard,
)
from custom_bots.utils.custom_message_texts import CustomMessageTexts
from database.config import (
    bot_db,
    product_db,
    order_db,
    product_review_db,
    user_db,
    custom_bot_user_db,
    mailing_db,
    user_role_db,
    option_db,
    order_option_db,
    channel_db,
)
from database.enums.language import AVAILABLE_LANGUAGES
from database.models.bot_model import BotIntegrityError, BotNotFoundError
from database.models.order_model import OrderSchema, OrderNotFoundError, OrderStatusValues
from database.models.option_model import OptionNotFoundError
from database.models.mailing_model import MailingNotFoundError
from database.models.product_model import ProductWithoutId, ProductNotFoundError
from database.models.user_role_model import UserRoleSchema, UserRoleValues
from database.models.post_message_model import PostMessageType
from database.models.product_review_model import ProductReviewNotFoundError

from logs.config import logger, extra_params

import json


@admin_bot_menu_router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    """Срабатывает, когда админ выбрал товар для отправки в канал"""

    data = json.loads(event.web_app_data.data)

    # _json: bool = True
    # if _json:
    #     data = json.loads(event.web_app_data.data)
    # else:
    #     data = event.web_app_data.data

    # data = {'bot_id': '1', 'product_id': 3}
    if data.get("product_id") is None:
        raise Exception("It is impossible")
    else:
        product_id = data["product_id"]

        try:
            product = await product_db.get_product(product_id)
        except ProductNotFoundError as e:
            logger.error("error while picking product for publish", exc_info=e)
            raise e

        try:
            bot_id = int(data["bot_id"])
            custom_bot = await bot_db.get_bot(bot_id)
            custom_bot_options = await option_db.get_option(custom_bot.options_id)
        except BotNotFoundError as e:
            logger.error("error while picking product for publish bot not found", exc_info=e)
            raise e
        except ValueError as e:
            logger.error("error while picking product for publish bot id not int", exc_info=e)
            raise e

        channels = await channel_db.get_all_channels(custom_bot.bot_id)
        if len(channels) == 0:
            return await event.answer(
                "У вас сейчас нет добавленных каналов\n\nДобавьте, после чего попробуйте опубликовать товар заново",
                reply_markup=await InlineChannelsListKeyboard.get_keyboard(custom_bot.bot_id),
            )
        custom_bot_data = await Bot(token=custom_bot.token).get_me()
        # TODO add language select for multi lang shops
        message = await event.answer_photo(
            photo=FSInputFile(f"{common_settings.FILES_PATH}{product.picture[0]}"),
            caption=MessageTexts.generate_publish_product(product),
            reply_markup=InlineModeProductKeyboardButton.get_keyboard(
                product_id=product_id, bot_username=custom_bot_data.username, lang=custom_bot_options.languages[0]
            ),
        )
        await message.reply(
            "Подтвердить отправление?",
            reply_markup=InlineAcceptPublishProductKeyboard.get_keyboard(
                custom_bot.bot_id, product_id, message.message_id
            ),
        )


@admin_bot_menu_router.callback_query(lambda query: InlineAcceptPublishProductKeyboard.callback_validator(query.data))
async def get_channel_for_publish(query: CallbackQuery):
    """Срабатывает когда пользователь (не) подтверждает отправление продукта в канал"""
    callback_data = InlineAcceptPublishProductKeyboard.Callback.model_validate_json(query.data)
    bot_id = callback_data.bot_id
    custom_bot = await bot_db.get_bot(bot_id)

    match callback_data.a:
        case callback_data.ActionEnum.ACCEPT:
            await query.answer("Выберите канал: ", show_alert=True)
            await query.message.delete()
            await query.message.answer(
                MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineChannelsListPublishKeyboard.get_keyboard(
                    custom_bot.bot_id, callback_data.pid, callback_data.msg_id
                ),
            )

        case callback_data.ActionEnum.REJECT:
            await query.message.answer("Отправка отменена")
            await query.message.delete()
            await query.message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, query.from_user.id),
            )


@admin_bot_menu_router.callback_query(lambda query: InlineChannelsListPublishKeyboard.callback_validator(query.data))
async def pick_channel_for_publish(query: CallbackQuery):
    callback_data = InlineChannelsListPublishKeyboard.Callback.model_validate_json(query.data)
    bot_id = callback_data.bot_id
    custom_bot = await bot_db.get_bot(bot_id)
    channel = await Bot(token=custom_bot.token).get_chat(callback_data.chid)

    match callback_data.a:
        case callback_data.ActionEnum.CANCEL:
            await query.message.answer("Отправка отменена")
            await query.message.delete()
            await query.message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, query.from_user.id),
            )
        case callback_data.ActionEnum.PICK_CHANNEL:
            await query.message.delete()
            await bot.send_message(
                chat_id=query.from_user.id,
                reply_to_message_id=callback_data.mid,
                text=f"Подтвердите отправку этого сообщения в канал @{channel.username}",
                reply_markup=InlineChannelPublishAcceptKeyboard.get_keyboard(
                    custom_bot.bot_id,
                    msg_id=callback_data.mid,
                    product_id=callback_data.pid,
                    channel_id=callback_data.chid,
                ),
            )


@admin_bot_menu_router.callback_query(lambda query: InlineChannelPublishAcceptKeyboard.callback_validator(query.data))
async def publish_product_in_channel(query: CallbackQuery):
    callback_data = InlineChannelPublishAcceptKeyboard.Callback.model_validate_json(query.data)
    bot_id = callback_data.bot_id
    custom_bot = await bot_db.get_bot(bot_id)
    custom_bot_options = await option_db.get_option(custom_bot.options_id)
    custom_tg_bot = Bot(token=custom_bot.token)

    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_CHANNEL_PICK:
            await query.answer("Выберите канал", show_alert=True)
            await query.message.delete()
            await query.message.answer(
                MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineChannelsListPublishKeyboard.get_keyboard(
                    custom_bot.bot_id, callback_data.mid, callback_data.pid
                ),
            )

        case callback_data.ActionEnum.SEND:
            try:
                product = await product_db.get_product(callback_data.pid)
            except ProductNotFoundError:
                await query.answer("Товар уже удален", show_alert=True)
                await query.message.delete()
                return
            await query.message.delete()
            # TODO add language select for multi lang shops
            await custom_tg_bot.send_photo(
                chat_id=callback_data.chid,
                photo=FSInputFile(f"{common_settings.FILES_PATH}{product.picture[0]}"),
                caption=MessageTexts.generate_publish_product(product),
                reply_markup=InlineModeProductKeyboardButton.get_keyboard(
                    product_id=callback_data.pid,
                    bot_username=(await custom_tg_bot.get_me()).username,
                    lang=custom_bot_options.languages[0],
                ),
            )


@admin_bot_menu_router.message(F.reply_to_message)
async def handle_reply_to_question(message: Message, state: FSMContext):
    """Срабатывает, когда админ в главном боте отвечает на вопрос от его клиента"""

    question_messages_data = QUESTION_MESSAGES.get_data()
    question_message_id = str(message.reply_to_message.message_id)
    if question_message_id not in question_messages_data:
        logger.info(
            f"{message.from_user.id}: "
            f"replied message with message_id {question_message_id} not found in question_messages_data"
        )
        return await bot_menu_handler(message, state)

    order_id = question_messages_data[question_message_id]["order_id"]
    try:
        order = await order_db.get_order(order_id)
    except OrderNotFoundError as e:
        logger.warning("", exc_info=e, extra=extra_params(user_id=message.from_user.id))
        return await message.answer(f"Заказ с номером №{order_id} не найден")

    custom_bot = await bot_db.get_bot_by_created_by(created_by=message.from_user.id)
    custom_bot_user = await custom_bot_user_db.get_custom_bot_user(custom_bot.bot_id, order.from_user)
    await Bot(token=custom_bot.token, default=BOT_PROPERTIES).send_message(
        chat_id=order.from_user,
        **CustomMessageTexts.get_response_text(custom_bot_user.user_language, order_id, message.text).as_kwargs(),
        reply_to_message_id=question_messages_data[question_message_id]["question_from_custom_bot_message_id"],
    )
    await message.answer("Ответ отправлен")

    del question_messages_data[question_message_id]
    QUESTION_MESSAGES.update_data(question_messages_data)
    user_state = FSMContext(
        storage=custom_bot_storage, key=StorageKey(chat_id=order.from_user, user_id=order.from_user, bot_id=bot.id)
    )
    user_state_data = await user_state.get_data()
    if "last_question_time" in user_state_data:
        del user_state_data["last_question_time"]
        await user_state.set_data(user_state_data)


@admin_bot_menu_router.callback_query(lambda query: InlineOrderCancelKeyboard.callback_validator(query.data))
async def handler_order_cancel_callback(query: CallbackQuery, state: FSMContext):
    """Подтверждение отмены заказа"""

    state_data = await state.get_data()
    bot_data = await bot_db.get_bot(state_data["bot_id"])
    bot_token = bot_data.token

    callback_data = InlineOrderCancelKeyboard.Callback.model_validate_json(query.data)

    custom_bot_user = await custom_bot_user_db.get_custom_bot_user(bot_data.bot_id, callback_data.chat_id)

    try:
        order = await order_db.get_order(callback_data.order_id)
    except OrderNotFoundError as e:
        logger.warning("", exc_info=e, extra=extra_params(user_id=query.from_user.id))
        await query.answer("Ошибка при работе с заказом, возможно статус уже изменился.", show_alert=True)
        return await query.message.edit_reply_markup(None)

    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_ORDER_STATUSES:
            await query.message.edit_reply_markup(
                reply_markup=InlineOrderStatusesKeyboard.get_keyboard(
                    callback_data.order_id, callback_data.msg_id, callback_data.chat_id, current_status=order.status
                )
            )
        case callback_data.ActionEnum.CANCEL:
            if order.status == OrderStatusValues.CANCELLED:
                return await query.answer("Этот статус уже выставлен")
            order.status = OrderStatusValues.CANCELLED

            await order_db.update_order(order)

            products = [
                (await product_db.get_product(int(product_id)), product_item.amount, product_item.used_extra_options)
                for product_id, product_item in order.items.items()
            ]

            text = await CommonMessageTexts.generate_order_notification_text(
                order, products, lang=custom_bot_user.user_language
            )

            # await Bot(bot_token, default=BOT_PROPERTIES).edit_message_text(
            #     order.convert_to_notification_text(products=products),
            #     reply_markup=None,
            #     chat_id=callback_data.chat_id,
            #     message_id=callback_data.msg_id
            # )
            await Bot(bot_token, default=BOT_PROPERTIES).edit_message_text(
                **text, reply_markup=None, chat_id=callback_data.chat_id, message_id=callback_data.msg_id
            )

            username = query.message.text[query.message.text.find("пользователя") :].split()[1].strip("\n")

            text = await CommonMessageTexts.generate_order_notification_text(order, products, username, True)

            await query.message.edit_text(**text, reply_markup=None)

            for item_id, item in order.items.items():
                product = await product_db.get_product(item_id)
                product.count += item.amount
                await product_db.update_product(product)

            await Bot(bot_token, default=BOT_PROPERTIES).send_message(
                chat_id=callback_data.chat_id,
                text=f"Новый статус заказа <b>#{order.id}</b>\n<b>{order.translate_order_status()}</b>",
            )


@admin_bot_menu_router.callback_query(lambda query: InlineAcceptReviewKeyboard.callback_validator(query.data))
async def handle_review_request(query: CallbackQuery):
    """Управление отзывом - принять или проигнорировать его"""

    callback_data = InlineAcceptReviewKeyboard.Callback.model_validate_json(query.data)
    try:
        review = await product_review_db.get_product_review(callback_data.product_review_id)
    except ProductReviewNotFoundError as e:
        logger.warning("", exc_info=e, extra=extra_params(user_id=query.from_user.id))
        return await query.answer("Продукт уже удален", show_alert=True)

    match callback_data.a:
        case callback_data.ActionEnum.SAVE:
            review.accepted = True
            await product_review_db.update_product_review(review)
            await query.answer("Отзыв сохранен", show_alert=True)
            text = query.message.text + "\n\nСтатус: ✅"
            await query.message.edit_text(text=text, reply_markup=None)

        case callback_data.ActionEnum.IGNORE:
            await product_review_db.delete_product_review(review.id)
            await query.answer("Отзыв проигнорирован", show_alert=True)
            text = query.message.text + "\n\nСтатус: ❌"
            await query.message.edit_text(text=text, reply_markup=None)


@admin_bot_menu_router.callback_query(lambda query: InlineOrderStatusesKeyboard.callback_validator(query.data))
async def handle_callback(query: CallbackQuery, state: FSMContext):
    """Изменение статуса заказа админом"""

    state_data = await state.get_data()
    bot_data = await bot_db.get_bot(state_data["bot_id"])
    bot_token = bot_data.token

    callback_data = InlineOrderStatusesKeyboard.Callback.model_validate_json(query.data)

    custom_bot_user = await custom_bot_user_db.get_custom_bot_user(bot_data.bot_id, callback_data.chat_id)

    try:
        order = await order_db.get_order(callback_data.order_id)
    except OrderNotFoundError as e:
        logger.warning("", exc_info=e, extra=extra_params(user_id=query.from_user.id))
        await query.answer("Ошибка при работе с заказом, возможно статус уже изменился.", show_alert=True)
        return await query.message.edit_reply_markup(None)

    match callback_data.a:
        case callback_data.ActionEnum.PRE_CANCEL:
            await query.message.edit_reply_markup(
                reply_markup=InlineOrderCancelKeyboard.get_keyboard(
                    callback_data.order_id,
                    callback_data.msg_id,
                    callback_data.chat_id,
                    lang=custom_bot_user.user_language,
                )
            )
        case (
            callback_data.ActionEnum.FINISH
            | callback_data.ActionEnum.PROCESS
            | callback_data.ActionEnum.BACKLOG
            | callback_data.ActionEnum.WAITING_PAYMENT
        ):  # noqa
            new_status = {
                callback_data.ActionEnum.FINISH: OrderStatusValues.FINISHED,
                callback_data.ActionEnum.PROCESS: OrderStatusValues.PROCESSING,
                callback_data.ActionEnum.BACKLOG: OrderStatusValues.BACKLOG,
                callback_data.ActionEnum.WAITING_PAYMENT: OrderStatusValues.WAITING_PAYMENT,
            }[callback_data.a]

            if order.status == new_status:
                return await query.answer("Этот статус уже выставлен")
            order.status = new_status

            await order_db.update_order(order)

            products = [
                (await product_db.get_product(int(product_id)), product_item.amount, product_item.used_extra_options)
                for product_id, product_item in order.items.items()
            ]
            # await Bot(bot_token, default=BOT_PROPERTIES).edit_message_text(
            #     order.convert_to_notification_text(products=products),
            #     reply_markup=None if callback_data.a == callback_data.ActionEnum.FINISH else
            #     InlineOrderCustomBotKeyboard.get_keyboard(order.id, callback_data.msg_id, callback_data.chat_id),
            #     chat_id=callback_data.chat_id,
            #     message_id=callback_data.msg_id
            # )
            text = await CommonMessageTexts.generate_order_notification_text(
                order, products, lang=custom_bot_user.user_language
            )
            await Bot(bot_token, default=BOT_PROPERTIES).edit_message_text(
                **text,
                reply_markup=None
                if callback_data.a == callback_data.ActionEnum.FINISH
                else InlineOrderCustomBotKeyboard.get_keyboard(
                    order.id, callback_data.msg_id, callback_data.chat_id, lang=custom_bot_user.user_language
                ),
                chat_id=callback_data.chat_id,
                message_id=callback_data.msg_id,
            )
            username = query.message.text[query.message.text.find("пользователя") :].split()[1].strip("\n")
            text = await CommonMessageTexts.generate_order_notification_text(order, products, username, True)
            await query.message.edit_text(
                **text,
                reply_markup=None
                if callback_data.a == callback_data.ActionEnum.FINISH
                else InlineOrderStatusesKeyboard.get_keyboard(
                    order.id, callback_data.msg_id, callback_data.chat_id, order.status
                ),
            )

            msg = await Bot(bot_token, default=BOT_PROPERTIES).send_message(
                chat_id=callback_data.chat_id,
                **CustomMessageTexts.get_new_order_status_text(
                    lang=custom_bot_user.user_language,
                    order_id=order.id,
                    status=order.translate_order_status(custom_bot_user.user_language),
                ).as_kwargs(),
            )
            try:
                options = await option_db.get_option(bot_data.options_id)
            except OptionNotFoundError:
                new_options_id = await create_bot_options()
                bot_data.options_id = new_options_id
                await bot_db.update_bot(bot_data)
                options = await option_db.get_option(new_options_id)
            if callback_data.a == callback_data.ActionEnum.FINISH:
                if options.auto_reduce is True:
                    zero_products = []
                    for item_id, item in order.items.items():
                        product = await product_db.get_product(item_id)
                        product.count = max(product.count - item.amount, 0)
                        await product_db.update_product(product)
                        if product.count == 0:
                            zero_products.append(product)
                    if zero_products:
                        await query.message.answer(**MessageTexts.generate_post_order_product_info(zero_products))

                await Bot(bot_token, default=BOT_PROPERTIES).send_message(
                    reply_to_message_id=msg.message_id,
                    chat_id=callback_data.chat_id,
                    **CustomMessageTexts.get_yuo_can_add_review_text(custom_bot_user.user_language).as_kwargs(),
                    reply_markup=InlineCreateReviewKeyboard.get_keyboard(
                        order_id=order.id, chat_id=callback_data.chat_id, lang=custom_bot_user.user_language
                    ),
                )


@admin_bot_menu_router.message(States.WAITING_FOR_TOKEN)
async def waiting_for_the_token_handler(message: Message, state: FSMContext):
    """Состояние, при котором у пользователя нет бота и от него требуется токен"""

    user_id = message.from_user.id
    user = await user_db.get_user(user_id)
    lang = user.locale
    token = message.text
    try:
        validate_token(token)

        found_bot = Bot(token)
        found_bot_data = await found_bot.get_me()
        bot_fullname, bot_username = found_bot_data.full_name, found_bot_data.username

        bot_id = await create_custom_bot(order_option_db, token, user_id, lang)

        await start_custom_bot(bot_id)
    except TokenValidationError:
        return await message.answer(MessageTexts.INCORRECT_BOT_TOKEN_MESSAGE.value)
    except TelegramUnauthorizedError:
        return await message.answer(MessageTexts.BOT_WITH_TOKEN_NOT_FOUND_MESSAGE.value)
    except BotIntegrityError as e:
        logger.warning("", exc_info=e, extra=extra_params(user_id=user_id))
        return await message.answer(
            "Бот с таким токеном в системе уже найден.\n"
            "Введите другой токен или перейдите в список ботов и поищите Вашего бота там"
        )
    except ClientConnectorError:
        logger.error("Cant connect to local api host (maybe service is offline)")
        return await message.answer("Сервис в данный момент недоступен, попробуйте еще раз позже")
    except Exception as e:
        logger.error(
            f"Unexpected error while adding new bot with token {token} from user {message.from_user.id}", exc_info=e
        )
        return await message.answer(":( Произошла ошибка при добавлении бота, попробуйте еще раз позже")
    user_bot = await bot_db.get_bot(bot_id)

    user_role = UserRoleSchema(user_id=user_id, bot_id=user_bot.bot_id, role=UserRoleValues.OWNER)
    try:
        await user_role_db.add_user_role(user_role)
    except IntegrityError:
        await user_role_db.update_user_role(user_role)
    logger.info(
        f"user_id={user_id} bot_id={bot_id} : set user role to owner for user " f"{user_id} of bot {bot_id}",
        extra=extra_params(user_id=user_id, bot_id=bot_id),
    )

    await message.answer(
        MessageTexts.BOT_INITIALIZING_MESSAGE.value.format(bot_fullname, bot_username),
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(),
    )
    await message.answer(
        MessageTexts.BOT_MENU_MESSAGE.value.format(bot_username),
        reply_markup=await InlineBotMenuKeyboard.get_keyboard(user_bot.bot_id, user_id),
    )

    await send_event(message.from_user, EventTypes.USER_CREATED_FIRST_BOT, event_bot=Bot(user_bot.token))

    await state.set_state(States.BOT_MENU)
    await state.set_data({"bot_id": bot_id})


@admin_bot_menu_router.message(States.BOT_MENU, F.photo)
async def bot_menu_photo_handler(message: Message, state: FSMContext):
    """Обрабатывает добавление товара через чат"""

    state_data = await state.get_data()
    photo_file_id = message.photo[-1].file_id

    if message.caption is None:
        return await message.answer(
            "Чтобы добавить товар, прикрепите его картинку и отправьте сообщение в виде:" "\n\nНазвание\nЦена в рублях"
        )

    params = message.caption.strip().split("\n")
    filename = "".join(sample(string.ascii_letters + string.digits, k=5)) + ".jpg"

    if len(params) != 2:
        return await message.answer(
            "Чтобы добавить товар, прикрепите его картинку и отправьте сообщение в виде:" "\n\nНазвание\nЦена в рублях"
        )

    if len(params[0]) > 100:
        return await message.answer(
            f"🚫 Название товара должно быть максимум из 100 символов\n\n" f"Длина вашего сообщения {len(params[0])}"
        )

    if params[-1].isdigit():
        price = int(params[-1])
    else:
        return await message.answer("Цена должна быть <b>целым числом</b>")

    await bot.download(photo_file_id, destination=f"{common_settings.FILES_PATH}{filename}")

    new_product = ProductWithoutId(
        bot_id=state_data["bot_id"],
        name=params[0],
        description="",
        price=price,
        count=0,
        picture=[filename],
        article=generate_article(),
        category=[0],
    )
    try:
        await product_db.add_product(new_product)
    except IntegrityError:
        return await message.answer("Товар с таким названием уже есть в боте.")
    await message.answer(
        "✅ Товар добавлен. Можно добавить ещё\n\n"
        "<i>* Более подробное управление товарами и гибкое добавление их</i> 👇",
        reply_markup=await InlineWebStockKeyboard.get_keyboard(state_data["bot_id"]),
    )


@admin_bot_menu_router.callback_query(lambda query: InlineBotMenuKeyboard.callback_validator(query.data))
async def bot_menu_callback_handler(query: CallbackQuery, state: FSMContext):
    """Обрабатывает главную клавиатуру меню бота"""

    state_data = await state.get_data()
    callback_data = InlineBotMenuKeyboard.Callback.model_validate_json(query.data)

    user_id = query.from_user.id
    bot_id = callback_data.bot_id
    db_bot_data = await bot_db.get_bot(bot_id)
    custom_tg_bot = Bot(token=db_bot_data.token)
    custom_bot_data = await custom_tg_bot.get_me()

    try:
        options = await option_db.get_option(db_bot_data.options_id)
    except OptionNotFoundError:
        new_options_id = await create_bot_options()
        db_bot_data.options_id = new_options_id
        await bot_db.update_bot(db_bot_data)
        options = await option_db.get_option(new_options_id)

    match callback_data.a:
        case callback_data.ActionEnum.BOT_SETTINGS:
            await query.message.edit_reply_markup(reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(bot_id))
        case callback_data.ActionEnum.ADMINS:
            await query.message.edit_reply_markup(
                reply_markup=await InlineAdministratorsManageKeyboard.get_keyboard(bot_id)
            )
        case callback_data.ActionEnum.LEAVE_ADMINISTRATING:
            await user_role_db.del_user_role(user_id, bot_id)
            await query.message.edit_text(
                "Вы больше не администратор этого бота. " "Пропишите /start для рестарта бота", reply_markup=None
            )
            await state.clear()
            await bot.send_message(
                db_bot_data.created_by,
                f"🔔 Пользователь больше не администратор ("
                f"{'@' + query.from_user.username if query.from_user.username else query.from_user.full_name}"
                f") для бота "
                f"@{custom_bot_data.username}",
            )
        case callback_data.ActionEnum.BOT_START:
            await start_custom_bot(bot_id)
            await query.message.edit_text(
                query.message.text,
                parse_mode=ParseMode.HTML,
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(bot_id, user_id),
            )
            await query.answer("Ваш бот запущен ✅", show_alert=True)
        case callback_data.ActionEnum.BOT_STOP:
            await stop_custom_bot(bot_id)
            await query.message.edit_text(
                query.message.text,
                parse_mode=ParseMode.HTML,
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(bot_id, user_id),
            )
            await query.answer("Ваш бот приостановлен ❌", show_alert=True)

        case callback_data.ActionEnum.REFERRAL_SYSTEM:
            from_chat_id = -1002218211760
            await bot.forward_messages(
                chat_id=query.from_user.id, from_chat_id=from_chat_id, message_ids=[10, 11, 12, 13]
            )
            await send_ref_user_info(query.message, query.from_user.id, bot)

        case callback_data.ActionEnum.BOT_DELETE:
            await query.message.answer(
                "Бот удалится вместе со всей базой продуктов безвозвратно.\n"
                "Напишите ПОДТВЕРДИТЬ для подтверждения удаления",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard(),
            )
            await query.answer()

            await state.set_state(States.DELETE_BOT)
            await state.set_data(state_data)
        case callback_data.ActionEnum.BOT_STATISTICS:
            users = await custom_bot_user_db.get_custom_bot_users(bot_id=bot_id)
            await query.message.answer(f"Статистика:\n\n" f"👨🏻‍🦱 Всего пользователей: {len(users)}")
            await query.answer()
        case callback_data.ActionEnum.MAILING_ADD | callback_data.ActionEnum.MAILING_OPEN:
            try:
                mailing = await mailing_db.get_mailing_by_bot_id(bot_id=bot_id)
                if callback_data.a == callback_data.ActionEnum.MAILING_ADD:
                    await query.answer("Рассылка уже создана", show_alert=True)
            except MailingNotFoundError:
                mailing = None

            if not mailing and callback_data.a == callback_data.ActionEnum.MAILING_ADD:
                await post_message_create(bot_id, PostMessageType.MAILING)

            custom_bot = await bot_db.get_bot(bot_id=bot_id)
            await query.message.edit_text(
                MessageTexts.bot_post_message_menu_message(PostMessageType.MAILING).format(
                    (await Bot(custom_bot.token).get_me()).username
                ),
                reply_markup=await InlinePostMessageMenuKeyboard.get_keyboard(
                    bot_id=bot_id, post_message_type=PostMessageType.MAILING, channel_id=None
                ),
            )
        case callback_data.ActionEnum.BOT_GOODS_OPEN:
            await query.message.edit_text(
                "Меню склада:", reply_markup=await InlineStockMenuKeyboard.get_keyboard(bot_id, options.auto_reduce)
            )
        case callback_data.ActionEnum.CHANNEL_LIST:
            custom_bot = await bot_db.get_bot(bot_id)

            await query.message.edit_text(
                MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineChannelsListKeyboard.get_keyboard(custom_bot.bot_id),
            )


@admin_bot_menu_router.callback_query(lambda query: InlineBackFromRefKeyboard.callback_validator(query.data))
async def back_to_main_menu(query: CallbackQuery):
    callback_data = InlineBackFromRefKeyboard.Callback.model_validate_json(query.data)
    bot_id = callback_data.bot_id
    user_bot = await bot_db.get_bot(bot_id)
    custom_bot_data = await Bot(token=user_bot.token).get_me()
    await query.message.edit_text(
        text=MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_data.username),
        reply_markup=await InlineBotMenuKeyboard.get_keyboard(callback_data.bot_id, query.from_user.id),
    )


@admin_bot_menu_router.callback_query(lambda query: InlineBotSettingsMenuKeyboard.callback_validator(query.data))
async def bot_settings_callback_handler(query: CallbackQuery, state: FSMContext):
    """Обрабатывает настройки кастомного бота"""

    state_data = await state.get_data()
    callback_data = InlineBotSettingsMenuKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id
    user_bot = await bot_db.get_bot(bot_id)
    custom_bot_data = await Bot(token=user_bot.token).get_me()
    bot_options = await option_db.get_option(user_bot.options_id)

    match callback_data.a:
        case callback_data.ActionEnum.GET_WEBAPP_URL:
            await _send_pinned_image(query, bot_id)
        case callback_data.ActionEnum.EDIT_ORDER_OPTIONS:
            order_options = await order_option_db.get_all_order_options(bot_id)
            await query.message.edit_text(
                **MessageTexts.generate_order_options_info(order_options),
                reply_markup=await InlineBotEditOrderOptionsKeyboard.get_keyboard(bot_id),
            )
            await query.answer("Раздел ещё в разработке, изменения будут сохраняться совсем скоро", show_alert=True)
        case callback_data.ActionEnum.BOT_EDIT_HELLO_TEXT:
            await query.message.answer(
                "Введите текст, который будет отображаться у пользователей Вашего бота "
                "при <b>первом обращении</b> и команде <b>/start</b>:",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard(),
            )
            await query.answer()
            await state.set_state(States.EDITING_START_MESSAGE)
            await state.set_data(state_data)
        case callback_data.ActionEnum.BOT_EDIT_EXPLANATION_TEXT:
            await query.message.answer(
                "Введите текст, который будет отображаться у пользователей Вашего бота "
                "при <b>любом</b> их сообщении: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard(),
            )
            await query.answer()
            await state.set_state(States.EDITING_DEFAULT_MESSAGE)
            await state.set_data(state_data)
        case callback_data.ActionEnum.PAYMENT_METHOD:
            await query.message.edit_text(
                MessageTexts.PAYMENT_METHOD_SETTINGS.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSettingsKeyboard.get_keyboard(user_bot.bot_id, user_bot.payment_type),
            )
        case callback_data.ActionEnum.EDIT_THEME:
            await query.message.edit_text(
                f"🎨 Кастомизация для бота @{custom_bot_data.username}.",
                reply_markup=InlineThemeSettingsMenuKeyboard.get_keyboard(bot_id),
            )
        case callback_data.ActionEnum.SELECT_SHOP_LANGUAGE:
            await query.message.edit_text(
                f"🌐 Выбор языка магазина для бота @{custom_bot_data.username}.",
                reply_markup=InlineSelectLanguageKb.get_keyboard(bot_id, AVAILABLE_LANGUAGES, bot_options.languages),
            )
        case callback_data.ActionEnum.BACK_TO_BOT_MENU:
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_data.username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(user_bot.bot_id, query.from_user.id),
            )


@admin_bot_menu_router.callback_query(lambda query: InlineSelectLanguageKb.callback_validator(query.data))
async def custom_bot_language_callback_handler(query: CallbackQuery):
    """Обрабатывает выбор языков кастомного бота"""

    callback_data = InlineSelectLanguageKb.Callback.model_validate_json(query.data)
    selected_lang = callback_data.selected

    bot_id = callback_data.bot_id
    user_bot = await bot_db.get_bot(bot_id)
    custom_bot_data = await Bot(token=user_bot.token).get_me()
    bot_options = await option_db.get_option(user_bot.bot_id)

    match callback_data.a:
        case callback_data.ActionEnum.BACK:
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_data.username),
                reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(callback_data.bot_id),
            )
        case callback_data.ActionEnum.SELECT:
            if selected_lang in bot_options.languages:
                if len(bot_options.languages) <= 1:
                    return await query.answer(MessageTexts.need_minimum_one_language(), show_alert=True)
                bot_options.languages.remove(selected_lang)
            else:
                bot_options.languages.append(selected_lang)
            await option_db.update_option(bot_options)
            await query.message.edit_reply_markup(
                reply_markup=InlineSelectLanguageKb.get_keyboard(bot_id, AVAILABLE_LANGUAGES, bot_options.languages)
            )


@admin_bot_menu_router.callback_query(lambda query: InlineAdministratorsManageKeyboard.callback_validator(query.data))
async def admins_manage_callback_handler(query: CallbackQuery):
    """Обрабатывает настройки администраторов бота"""

    callback_data = InlineAdministratorsManageKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id
    user_bot = await bot_db.get_bot(bot_id)
    custom_bot_data = await Bot(token=user_bot.token).get_me()

    main_bot_data = await query.bot.get_me()

    match callback_data.a:
        case callback_data.ActionEnum.ADD_ADMIN:
            link_hash, link = generate_admin_invite_link(main_bot_data.username)
            user_bot.admin_invite_link_hash = link_hash
            await bot_db.update_bot(user_bot)

            add_admin_link_text = Text(
                "Администраторы бота ",
                Bold("@" + main_bot_data.username),
                ":",
                "\n\nℹ️ Для добавления администратора в бота отправьте нужному ",
                "пользователю ссылку приглашение:\n",
                Bold(link),
                "\n\n",
                "Сгенерированная ссылка ",
                Italic("действует 1 раз"),
                " для создания новой ссылки нажмите на кнопку добавить админа еще раз.",
            )

            await query.message.edit_text(
                **add_admin_link_text.as_kwargs(),
                reply_markup=await InlineAdministratorsManageKeyboard.get_keyboard(bot_id),
                disable_web_page_preview=True,
            )
        case callback_data.ActionEnum.ADMIN_LIST:
            admins = await user_role_db.get_bot_admin_ids(bot_id)
            admins_text = ""
            for ind, admin in enumerate(admins, start=1):
                admin_user = await bot.get_chat(admin)
                admins_text += (
                    f"=== {ind} ===\n"
                    f"👤 Имя: {admin_user.full_name}\n🆔 UID: {admin_user.id}"
                    f"\n🔤 Username: @{admin_user.username}\n\n"
                )
            if not admins:
                admins_text = Bold("Администраторы еще не добавлены")
            else:
                admins_text += "Для удаления админа введите команду:\n/rm_admin UID"

            admins_list_text = Text("Администраторы бота ", Bold("@" + main_bot_data.username), ":\n\n", admins_text)

            text, entities = admins_list_text.render()
            if text != query.message.text:
                await query.message.edit_text(
                    **admins_list_text.as_kwargs(),
                    reply_markup=await InlineAdministratorsManageKeyboard.get_keyboard(bot_id),
                    disable_web_page_preview=True,
                )
            else:
                await query.answer()
        case callback_data.ActionEnum.BACK_TO_BOT_MENU:
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_data.username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(user_bot.bot_id, query.from_user.id),
            )


@admin_bot_menu_router.message(States.BOT_MENU)
async def bot_menu_handler(message: Message, state: FSMContext):
    """Срабатывает, если админ просто написал сообщение. Указывает администратору что делать."""

    state_data = await state.get_data()
    if "bot_id" in state_data and state_data["bot_id"] == -1:
        await state.set_state(States.WAITING_FOR_TOKEN)
        await greetings_message(bot, None, message)
        return await message.answer("Ваш список ботов пуст, используйте инструкцию выше 👆")
    custom_bot = await bot_db.get_bot(state_data["bot_id"])

    match message.text:
        case ReplyBotMenuKeyboard.Callback.ActionEnum.SHOP.value:
            await message.answer(
                "Кнопка для входа в магазин 👇", reply_markup=InlineBotMainWebAppButton.get_keyboard(custom_bot.bot_id)
            )
        case ReplyBotMenuKeyboard.Callback.ActionEnum.SETTINGS.value:
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id),
            )

        case ReplyBotMenuKeyboard.Callback.ActionEnum.CONTACTS.value:
            await message.answer(MessageTexts.CONTACTS.value)
        case _:
            await message.answer(
                "Для навигации используйте кнопки 👇", reply_markup=ReplyBotMenuKeyboard.get_keyboard()
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id),
            )


async def send_new_order_notify(order: OrderSchema, user_id: int):
    """Sends demo order notifications to the admin"""

    order_user_data = await bot.get_chat(order.from_user)

    products = []
    for product_id, order_item in order.items.items():
        product = await product_db.get_product(product_id)
        products.append((product, order_item.amount, order_item.used_extra_options))

    text = await CommonMessageTexts.generate_order_notification_text(
        order, products, "@" + order_user_data.username if order_user_data.username else order_user_data.full_name, True
    )
    await bot.send_message(user_id, "Так будет выглядеть у тебя уведомление о новом заказе 👇")
    await bot.send_message(chat_id=user_id, **text)


async def send_order_change_status_notify(order: OrderSchema):
    """Sends notification about changed status of specific order"""

    user_bot = await bot_db.get_bot(order.bot_id)
    text = f"Новый статус заказ <b>#{order.id}</b>\n<b>{order.status}</b>"
    await bot.send_message(user_bot.created_by, text)
    await bot.send_message(order.from_user, text)


async def _send_pinned_image(query: CallbackQuery, bot_id: int) -> None:
    file_ids = cache_resources_file_id_store.get_data()
    file_name = "pinned_webapp.png"

    try:
        await query.message.answer_photo(
            caption=MessageTexts.get_web_app_url(bot_id=bot_id),
            photo=file_ids[file_name],
        )
    except (TelegramBadRequest, KeyError) as e:
        logger.info(f"error while sending {file_name}.... cache is empty, sending raw files {e}")
        photo_message = await query.message.answer_photo(
            caption=MessageTexts.get_web_app_url(bot_id=bot_id),
            photo=FSInputFile(common_settings.RESOURCES_PATH.format(file_name)),
        )
        file_ids[file_name] = photo_message.photo[-1].file_id
        cache_resources_file_id_store.update_data(file_ids)
