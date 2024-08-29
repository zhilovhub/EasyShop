import json

from aiogram import F, Bot
from aiogram.types import Message

from custom_bots.multibot import CustomUserStates, main_bot
from custom_bots.utils.utils import format_locales
from custom_bots.handlers.routers import multi_bot_router
from custom_bots.utils.order_creation import order_creation_process
from custom_bots.utils.custom_message_texts import CustomMessageTexts
from custom_bots.keyboards.custom_bot_menu_keyboards import ReplyCustomBotMenuKeyboard

from common_utils.keyboards.keyboards import InlineBotMainWebAppButton
from common_utils.bot_utils import create_bot_options
from common_utils.order_utils.order_type import OrderType
from common_utils.order_utils.order_utils import create_order

from database.enums import UserLanguageValues
from database.config import bot_db, option_db
from database.models.bot_model import BotNotFoundError
from database.models.option_model import OptionNotFoundError
from database.models.product_model import NotEnoughProductsInStockToReduce

from logs.config import custom_bot_logger, extra_params


@multi_bot_router.message(F.web_app_data)
async def process_web_app_request(event: Message, lang: UserLanguageValues):
    user_id = event.from_user.id
    order_user_data = await event.bot.get_chat(user_id)

    try:
        order = await create_order(event.from_user.id, event.web_app_data.data, OrderType.CUSTOM_BOT_ORDER)
        await order_creation_process(order, order_user_data)
    except NotEnoughProductsInStockToReduce as e:
        await event.answer(**CustomMessageTexts.get_not_enough_in_stock_err_message(lang, e.product.name).as_kwargs())
    except Exception as e:
        await event.answer(**CustomMessageTexts.get_order_creation_err_message(lang).as_kwargs())

        try:
            data = json.loads(event.web_app_data.data)
            bot_id = data["bot_id"]
        except Exception as another_e:
            bot_id = -1
            custom_bot_logger.error(
                f"user_id={user_id}: Unable to find bot_id from event.web_app_data.data",
                extra=extra_params(user_id=user_id),
                exc_info=another_e,
            )

        custom_bot_logger.error(
            f"user_id={user_id}: Unable to create an order in bot_id={bot_id}",
            extra=extra_params(user_id=user_id, bot_id=bot_id),
            exc_info=e,
        )
        raise e


@multi_bot_router.message(CustomUserStates.MAIN_MENU)
async def main_menu_handler(message: Message, lang: UserLanguageValues):
    try:
        bot = await bot_db.get_bot_by_token(message.bot.token)
    except BotNotFoundError:
        custom_bot_logger.warning(
            f"bot_token={message.bot.token}: this bot is not in db", extra=extra_params(bot_token=message.bot.token)
        )
        await Bot(message.bot.token).delete_webhook()
        return await message.answer(**CustomMessageTexts.get_bot_not_init_message(lang).as_kwargs())
    main_bot_data = await main_bot.get_me()

    shop_actions = ReplyCustomBotMenuKeyboard.Callback.ActionEnum
    match message.text:
        case shop_actions.SHOP.value | shop_actions.SHOP_ENG.value | shop_actions.SHOP_HEB.value:
            await message.answer(
                **CustomMessageTexts.get_shop_button_message(lang).as_kwargs(),
                reply_markup=InlineBotMainWebAppButton.get_keyboard(bot.bot_id, lang),
            )
        case _:
            try:
                options = await option_db.get_option(bot.options_id)
            except OptionNotFoundError:
                new_options_id = await create_bot_options()
                bot.options_id = new_options_id
                await bot_db.update_bot(bot)
                options = await option_db.get_option(new_options_id)

            default_msg = options.default_msg

            await message.answer(
                format_locales(default_msg[lang.value], message.from_user, message.chat, bot_data=main_bot_data),
                reply_markup=ReplyCustomBotMenuKeyboard.get_keyboard(lang),
            )
