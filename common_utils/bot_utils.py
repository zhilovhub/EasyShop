from database.config import bot_db, option_db
from database.models.bot_model import BotIntegrityError, BotSchemaWithoutId
from database.models.option_model import OptionSchemaWithoutId
from database.models.order_option_model import OrderOptionSchemaWithoutId, OrderOptionDao, OrderOptionTypeValues

from bot.utils.message_texts import MessageTexts

from datetime import datetime


async def create_order_options(order_option_db: OrderOptionDao, bot_id: int):
    """
    Creates default order options
    """
    await order_option_db.add_order_option(
        OrderOptionSchemaWithoutId(
            bot_id=bot_id,
            option_name="Имя клиента",
            hint="Иванов Иван",
            required=True,
            emoji="👤",
            position_index=1,
        )
    )

    await order_option_db.add_order_option(
        OrderOptionSchemaWithoutId(
            bot_id=bot_id,
            option_name="Номер телефона",
            hint="Номер телефона",
            required=True,
            emoji="📱",
            position_index=2,
        )
    )

    await order_option_db.add_order_option(
        OrderOptionSchemaWithoutId(
            bot_id=bot_id,
            option_name="Город",
            hint="г.Москва",
            required=True,
            emoji="🌇",
            position_index=3,
        )
    )

    await order_option_db.add_order_option(
        OrderOptionSchemaWithoutId(
            bot_id=bot_id,
            option_name="Адрес доставки",
            hint="Дмитровское шоссе, 81",
            required=True,
            emoji="🛤",
            position_index=4,
        )
    )

    await order_option_db.add_order_option(
        OrderOptionSchemaWithoutId(
            bot_id=bot_id,
            option_name="Способ доставки",
            hint="Выберете способ доставки",
            required=True,
            emoji="🚐",
            position_index=5,
            option_type=OrderOptionTypeValues.CHOOSE,
        )
    )

    await order_option_db.add_order_option(
        OrderOptionSchemaWithoutId(
            bot_id=bot_id,
            option_name="Время доставки",
            hint="Предпочтения по времени доставки",
            required=True,
            emoji="⏰",
            position_index=6,
        )
    )

    await order_option_db.add_order_option(
        OrderOptionSchemaWithoutId(
            bot_id=bot_id,
            option_name="Комментарий",
            hint="Добавьте комментарий",
            required=True,
            emoji="💌",
            position_index=7,
            option_type=OrderOptionTypeValues.TEXT_AREA,
        )
    )


async def create_bot_options() -> int:
    """
    Creates new option
    """
    new_option_id = await option_db.add_option(
        OptionSchemaWithoutId(
            web_app_button=MessageTexts.OPEN_WEB_APP_BUTTON_TEXT.value,
        )
    )

    return new_option_id


async def create_custom_bot(order_option_db: OrderOptionDao, token: str, user_id: int, lang: str) -> int:
    """
    Creates bot with default options
    :returns: bot_id
    :raises BotIntegrityError: bot token already registered
    """
    new_option_id = await create_bot_options()
    try:
        new_bot = BotSchemaWithoutId(
            bot_token=token,  # noqa
            status="new",
            created_at=datetime.utcnow(),
            created_by=user_id,
            locale=lang,
            options_id=new_option_id,
        )
        bot_id = await bot_db.add_bot(new_bot)
    except BotIntegrityError as e:
        await option_db.delete_option(new_option_id)
        raise e
    await create_order_options(order_option_db, bot_id)
    return bot_id
