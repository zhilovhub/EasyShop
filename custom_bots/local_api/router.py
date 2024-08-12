import json

from aiogram import Bot
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent

from bot.handlers.admin_bot_menu_handlers import send_new_order_notify
from custom_bots.multibot import web, session, OTHER_BOTS_URL, main_bot
from custom_bots.utils.utils import is_bot_token
from custom_bots.utils.order_creation import order_creation_process

from common_utils.order_utils.order_type import OrderType
from common_utils.order_utils.order_utils import create_order

from database.config import bot_db
from database.models.bot_model import BotNotFoundError
from database.models.product_model import NotEnoughProductsInStockToReduce

from logs.config import custom_bot_logger, extra_params, logger

routes = web.RouteTableDef()


@routes.get('/start_bot/{bot_id}')
async def add_bot_handler(request):
    bot_id = request.match_info['bot_id']
    try:
        bot = await bot_db.get_bot(int(bot_id))
    except BotNotFoundError:
        return web.Response(status=404, text=f"Bot with provided id not found (id: {bot_id}).")
    if not is_bot_token(bot.token):
        return web.Response(status=400, text="Incorrect bot token format.")
    try:
        new_bot = Bot(token=bot.token, session=session)
        new_bot_data = await new_bot.get_me()
    except TelegramUnauthorizedError:
        return web.Response(status=400, text="Unauthorized telegram token.")

    await new_bot.delete_webhook(drop_pending_updates=True)
    custom_bot_logger.debug(
        f"bot_id={bot_id}: webhook is deleted",
        extra=extra_params(bot_id=bot_id)
    )

    result = await new_bot.set_webhook(
        OTHER_BOTS_URL.format(bot_token=bot.token),
        allowed_updates=["message", "my_chat_member",
                         "callback_query", "chat_member", "channel_post",
                         "inline_query", "pre_checkout_query", "shipping_query"]
    )
    if result:
        custom_bot_logger.debug(
            f"bot_id={bot_id}: webhook is set",
            extra=extra_params(bot_id=bot_id)
        )
    else:
        custom_bot_logger.warning(
            f"bot_id={bot_id}: webhook's setting is failed",
            extra=extra_params(bot_id=bot_id)
        )

    return web.Response(text=f"Started bot with token ({bot.token}) and username (@{new_bot_data.username})")


@routes.get('/stop_bot/{bot_id}')
async def stop_bot_handler(request):
    bot_id = request.match_info['bot_id']
    try:
        bot = await bot_db.get_bot(int(bot_id))
    except BotNotFoundError:
        return web.Response(status=404, text=f"Bot with provided id not found (id: {bot_id}).")
    if not is_bot_token(bot.token):
        return web.Response(status=400, text="Incorrect bot token format.")

    try:
        new_bot = Bot(token=bot.token, session=session)
        new_bot_data = await new_bot.get_me()

    except TelegramUnauthorizedError:
        return web.Response(status=400, text="Unauthorized telegram token.")

    await new_bot.delete_webhook(drop_pending_updates=True)
    custom_bot_logger.debug(
        f"bot_id={bot_id}: webhook is deleted",
        extra=extra_params(bot_id=bot_id)
    )

    return web.Response(text=f"Stopped bot with token ({bot.token}) and username (@{new_bot_data.username})")


@routes.post('/send_web_app_data_to_bot/{bot_id}')
async def send_web_app_data_to_bot(request):
    custom_bot_logger.debug(f"new request to send_web_app_data_to_bot : {request}")

    bot_id = request.match_info['bot_id']
    custom_bot_logger.debug(f"new request to with bot_id : {bot_id}")
    try:
        bot = await bot_db.get_bot(int(bot_id))
        custom_bot_logger.debug(f"new request to with bot : {bot}")
    except BotNotFoundError:
        return web.Response(status=404, text=f"Bot with provided id not found (id: {bot_id}).")
    if not is_bot_token(bot.token):
        return web.Response(status=400, text="Incorrect bot token format.")

    custom_bot_tg = Bot(bot.token)
    custom_bot_logger.debug(f"new request to with tg_bot : {custom_bot_tg}")
    sent_data = await request.json()
    custom_bot_logger.debug(f"new request to with sent_data : {sent_data}")

    user_id = sent_data["from_user"]
    order_type = sent_data["order_type"]

    invoice_link = None

    match order_type:
        case OrderType.MAIN_BOT_TEST_ORDER.value:
            try:
                order = await create_order(user_id, sent_data, OrderType.MAIN_BOT_TEST_ORDER, _json=False)

                logger.info(f"order with id #{order.id} created")
            except NotEnoughProductsInStockToReduce as e:
                logger.info("not enough items for order creation")
                return await main_bot.send_message(
                    chat_id=user_id,
                    text=f"К сожалению на складе недостаточно <b>{e.product.name}</b> для выполнения Вашего заказа.")
            except Exception as e:
                logger.error("error while creating order", exc_info=e)
                raise e
            try:
                await send_new_order_notify(order, user_id)
            except Exception as e:
                logger.error("error while sending test order notification", exc_info=e)
                raise e
        case OrderType.CUSTOM_BOT_ORDER.value:
            try:
                order = await create_order(user_id, sent_data, OrderType.CUSTOM_BOT_ORDER, _json=False)
                order_user_data = await custom_bot_tg.get_chat(user_id)
                invoice_link = await order_creation_process(order, order_user_data)
            except NotEnoughProductsInStockToReduce as e:
                await custom_bot_tg.send_message(
                    chat_id=user_id,
                    text=f"К сожалению на складе недостаточно <b>{e.product.name}</b> для выполнения Вашего заказа."
                )
            except Exception as e:
                await custom_bot_tg.send_message(
                    chat_id=user_id,
                    text="Произошла ошибка при создании заказа, администраторы уведомлены."
                )

                try:
                    data = json.loads(sent_data)
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

            try:
                return web.Response(status=200,
                                    body=json.dumps({"invoice_url": invoice_link}),
                                    content_type='application/json')
            except Exception as e:
                custom_bot_logger.error("error while sending response from local Api", exc_info=e)


@routes.post('/send_hex_color_to_bot')
async def send_hex_data_to_bot(request):
    custom_bot_logger.debug(f"new request to send_hex_color_to_bot : {request}")
    try:
        data = await request.json()

        await main_bot.answer_web_app_query(web_app_query_id=data['query_id'],
                                            result=InlineQueryResultArticle(
                                                id="hex_color",
                                                title="hex_color",
                                                input_message_content=InputTextMessageContent(
                                                    message_text=data['color']
                                                )
                                            ))
    except Exception as ex:
        custom_bot_logger.error(
            f"error on processing local api send hex request", exc_info=True
        )
        raise ex

    return web.Response(status=200, text=f"Data was sent to bot successfully")
