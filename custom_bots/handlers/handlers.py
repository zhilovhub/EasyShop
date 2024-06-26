import json
import random
import string
from datetime import datetime, timedelta

from aiogram import F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.keyboards import keyboards
from bot.utils.message_texts import MessageTexts
from bot.keyboards.order_manage_keyboards import InlineOrderStatusesKeyboard, InlineOrderCustomBotKeyboard
from bot.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard

from custom_bots.multibot import order_db, product_db, bot_db, main_bot, PREV_ORDER_MSGS, custom_bot_user_db, \
    CustomUserStates, format_locales, channel_db, custom_ad_db, scheduler, user_db
from custom_bots.handlers.routers import multi_bot_router
from custom_bots.utils.custom_bot_options import get_option

from database.models.bot_model import BotNotFound
from database.models.order_model import OrderSchema, OrderItem
from database.models.product_model import NotEnoughProductsInStockToReduce
from database.models.custom_ad_model import CustomAdSchemaWithoutId

from logs.config import custom_bot_logger, extra_params


@multi_bot_router.message(F.web_app_data)
async def process_web_app_request(event: Message):
    user_id = event.from_user.id
    order_user_data = await event.bot.get_chat(user_id)

    try:
        data = json.loads(event.web_app_data.data)

        bot_id = data["bot_id"]
        bot_data = await bot_db.get_bot(int(bot_id))

        custom_bot_logger.info(
            f"user_id={user_id}: received web app data: {data}",
            extra=extra_params(user_id=user_id, bot_id=bot_id)
        )

        data["from_user"] = user_id
        data["payment_method"] = "Картой Онлайн"
        data["status"] = "backlog"

        items: dict[int, OrderItem] = {}

        zero_products = []

        for item_id, item in data['raw_items'].items():
            product = await product_db.get_product(item_id)
            chosen_options = {}
            used_options = False
            if 'chosen_option' in item and item['chosen_option']:
                used_options = True
                option_title = list(product.extra_options.items())[0][0]
                chosen_options[option_title] = item['chosen_option']
            items[item_id] = OrderItem(amount=item['amount'], used_extra_option=used_options,
                                       extra_options=chosen_options)
            if bot_data.settings and "auto_reduce" in bot_data.settings and bot_data.settings["auto_reduce"]:
                if product.count < item['amount']:
                    raise NotEnoughProductsInStockToReduce(product, item['amount'])
                product.count -= item['amount']
                if product.count == 0:
                    zero_products.append(product)
                await product_db.update_product(product)

        if zero_products:
            msg = await main_bot.send_message(bot_data.created_by,
                                              "⚠️ Внимание, после этого заказа кол-во следующих товаров будет равно 0.")
            await msg.reply("\n".join([f"{p.name} [{p.id}]" for p in zero_products]))

        data['items'] = items

        date = datetime.now().strftime("%d%m%y")
        random_string = ''.join(random.sample(
            string.digits + string.ascii_letters, 5))
        data['order_id'] = date + random_string

        order = OrderSchema(**data)
        order.ordered_at = order.ordered_at.replace(tzinfo=None)

        await order_db.add_order(order)

        products = [(await product_db.get_product(product_id), product_item.amount, product_item.extra_options)
                    for product_id, product_item in order.items.items()]
        username = "@" + order_user_data.username if order_user_data.username else order_user_data.full_name
        admin_id = (await bot_db.get_bot_by_token(event.bot.token)).created_by
        main_msg = await main_bot.send_message(
            admin_id, order.convert_to_notification_text(
                products,
                username,
                True
            ))

        msg_id_data = PREV_ORDER_MSGS.get_data()
        msg_id_data[order.id] = (main_msg.chat.id, main_msg.message_id)
        PREV_ORDER_MSGS.update_data(msg_id_data)
        msg = await event.bot.send_message(
            user_id, order.convert_to_notification_text(
                products,
                username,
                False
            ), reply_markup=InlineOrderCustomBotKeyboard.get_keyboard(order.id)
        )
        await main_bot.edit_message_reply_markup(
            main_msg.chat.id,
            main_msg.message_id,
            reply_markup=InlineOrderStatusesKeyboard.get_keyboard(
                order.id, msg.message_id, msg.chat.id, current_status=order.status
            )
        )

        custom_bot_logger.info(
            f"user_id={user_id}: order with order_id {order.id} is created",
            extra=extra_params(
                user_id=user_id, bot_id=bot_id, order_id=order.id)
        )
    except NotEnoughProductsInStockToReduce as e:
        await event.answer(
            f":(\nК сожалению на складе недостаточно <b>{e.product.name}</b> для выполнения Вашего заказа."
        )
    except Exception as e:
        await event.answer("Произошла ошибка при создании заказа, администраторы уведомлены.")

        try:
            data = json.loads(event.web_app_data.data)
            bot_id = data["bot_id"]
        except Exception as another_e:
            bot_id = -1
            custom_bot_logger.error(
                f"user_id={user_id}: Unable to find bot_id from event.web_app_data.data",
                extra=extra_params(user_id=user_id),
                exc_info=another_e
            )

        custom_bot_logger.error(
            f"user_id={user_id}: Unable to create an order in bot_id={bot_id}",
            extra=extra_params(user_id=user_id, bot_id=bot_id),
            exc_info=e
        )
        raise e


@multi_bot_router.callback_query(lambda q: q.data.startswith("request_ad"))
async def request_ad_handler(query: CallbackQuery):
    bot_id = int(query.data.split(':')[-1])
    bot_data = await bot_db.get_bot(bot_id)
    admin_user = await query.bot.get_chat(bot_data.created_by)
    await query.message.edit_text("Правила размещения рекламы:\n1. ...\n2. ...\n3. ...",
                                  reply_markup=keyboards.get_request_ad_keyboard(bot_id, admin_user.username))


@multi_bot_router.callback_query(lambda q: q.data.startswith("accept_ad"))
async def accept_ad_handler(query: CallbackQuery):
    bot_id = int(query.data.split(':')[-1])
    msg = await query.message.answer_photo(photo=FSInputFile("ad_example.jpg"),
                                           caption=MessageTexts.EXAMPLE_AD_POST_TEXT.value)
    await msg.reply("Условия для принятия:\n1. В канале должно быть 3 и более подписчиков."
                    "\n2. В течении 5 минут после рекламного поста нельзя публиковать посты."
                    "\n3. Время сделки: 10м."
                    "\n4. Стоимость: 1000руб.",
                    reply_markup=await keyboards.get_accept_ad_keyboard(bot_id))


@multi_bot_router.callback_query(lambda q: q.data.startswith("continue_ad_accept"))
async def continue_ad_accept_handler(query: CallbackQuery):
    bot_id = int(query.data.split(':')[-1])
    await query.message.edit_text("Выберите канал для отправки рекламного сообщения.",
                                  reply_markup=await keyboards.get_custom_bot_ad_channels_list_keyboard(bot_id))


@multi_bot_router.callback_query(lambda q: q.data.startswith("back_to_partnership"))
async def back_to_partnership(query: CallbackQuery):
    bot_id = int(query.data.split(':')[-1])
    await query.message.edit_text(MessageTexts.CUSTOM_BOT_PARTNERSHIP.value,
                                  reply_markup=keyboards.get_partnership_inline_kb(bot_id))


async def complete_custom_ad_request(channel_id: int, bot_id: int):
    bot_data = await bot_db.get_bot(bot_id)
    bot = Bot(token=bot_data.token)

    adv = await custom_ad_db.get_channel_last_custom_ad(channel_id=channel_id)
    adv.status = "finished"

    channel = await channel_db.get_channel(channel_id)
    channel.is_ad_post_block = False
    await channel_db.update_channel(channel)

    await bot.send_message(adv.by_user, "Рекламное предложение завершено, на Ваш баланс зачислено 1000руб.")

    user = await custom_bot_user_db.get_custom_bot_user(bot_id, adv.by_user)
    user.balance += 1000

    admin_user = await user_db.get_user(bot_data.created_by)
    admin_user.balance -= 1000

    await user_db.update_user(admin_user)
    await custom_bot_user_db.update_custom_bot_user(user)


@multi_bot_router.callback_query(lambda q: q.data.startswith("ad_channel"))
async def ad_channel_handler(query: CallbackQuery):
    bot_id = int(query.data.split(':')[-2])
    channel_id = int(query.data.split(':')[-1])
    channel = await channel_db.get_channel(channel_id)
    channel_chat = await query.bot.get_chat(channel_id)
    members_count = await channel_chat.get_member_count()
    bot_data = await bot_db.get_bot(bot_id)
    admin_user = await user_db.get_user(bot_data.created_by)
    if admin_user.balance < 1000:
        return await query.answer("В данный момент администратор канала не готов принимать рекламные предложения"
                                  " (на балансе нет средств)")
    if members_count < 3:
        return await query.answer(f"В этом канале не достаточно подписчиков. ({members_count} < 3)",
                                  show_alert=True)
    msg = await query.bot.send_photo(chat_id=channel_id,
                                     photo=FSInputFile("ad_example.jpg"),
                                     caption=MessageTexts.EXAMPLE_AD_POST_TEXT.value)
    await query.message.edit_text("Сообщение отправлено в канал. Для завершения сделки, "
                                  "продолжайте соблюдать условия."
                                  "\n1. В канале должно быть 3 и более подписчиков."
                                  "\n2. В течении 5 минут после рекламного поста нельзя публиковать посты."
                                  "\n3. Время сделки: 10мин."
                                  "\n4. Стоимость: 1000руб.", reply_markup=None)
    channel.is_ad_post_block = True
    channel.ad_post_block_until = datetime.now() + timedelta(minutes=5)
    await channel_db.update_channel(channel)
    job_id = await scheduler.add_scheduled_job(complete_custom_ad_request,
                                               (datetime.now() + timedelta(minutes=10)).replace(tzinfo=None),
                                               [channel.channel_id, bot_id])
    await custom_ad_db.add_ad(CustomAdSchemaWithoutId(channel_id=channel.channel_id,
                                                      message_id=msg.message_id,
                                                      time_until=datetime.now() + timedelta(minutes=10),
                                                      status="active",
                                                      finish_job_id=job_id,
                                                      by_user=query.from_user.id))


@multi_bot_router.message(CustomUserStates.MAIN_MENU)
async def main_menu_handler(message: Message):
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
    except BotNotFound:
        custom_bot_logger.warning(
            f"bot_token={message.bot.token}: this bot is not in db",
            extra=extra_params(bot_token=message.bot.token)
        )
        return await message.answer("Бот не инициализирован")

    match message.text:
        case ReplyCustomBotMenuKeyboard.Callback.ActionEnum.PARTNER_SHIP.value:
            bot_id = (await bot_db.get_bot_by_token(message.bot.token)).bot_id
            await message.answer(MessageTexts.CUSTOM_BOT_PARTNERSHIP.value,
                                 reply_markup=keyboards.get_partnership_inline_kb(bot_id))
        case _:
            default_msg = await get_option("default_msg", message.bot.token)

            await message.answer(
                format_locales(default_msg, message.from_user, message.chat),
                reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(
                    bot.bot_id
                )
            )
