import aiohttp


from fastapi import APIRouter

from pydantic import BaseModel

from database.config import bot_db, option_db, order_option_db, order_choose_option_db
from database.models.bot_model import BotNotFoundError
from database.models.option_model import OptionSchema, OptionNotFoundError
from database.models.order_option_model import OrderOptionSchema, OrderOptionTypeValues
from database.models.order_choose_option_model import OrderChooseOptionSchema

from api.utils import HTTPBotNotFoundError, HTTPInternalError, RESPONSES_DICT

from common_utils.themes import ThemeParamsSchema
from common_utils.config import custom_telegram_bot_settings
from common_utils.exceptions.local_api_exceptions import LocalAPIException

from logs.config import api_logger, extra_params

PATH = "/settings"
router = APIRouter(
    prefix=PATH,
    tags=["settings"],
    responses=RESPONSES_DICT,
)


@router.get("/get_web_app_options/{bot_id}/")
async def get_web_app_options_api(bot_id: int) -> OptionSchema:
    """
    :returns: Pydantic WebAppOptions Model with options

    :raises HTTPBotNotFoundError:
    :raises HTTPInternalError:
    """
    try:
        bot = await bot_db.get_bot(bot_id)
        options = await option_db.get_option(bot.options_id)

        return options
    except BotNotFoundError as e:
        api_logger.error(
            f"bot_id={bot_id}: bot_id={bot_id} is not found in database", extra=extra_params(bot_id=bot_id), exc_info=e
        )
        raise HTTPBotNotFoundError(bot_id=bot_id)
    except OptionNotFoundError as e:
        api_logger.error(
            f"bot_id={bot_id}: options is not found in database returning default options",
            extra=extra_params(bot_id=bot_id),
            exc_info=e,
        )
        return OptionSchema(
            id=-1,
            start_msg="None",
            default_msg="None",
            post_order_msg=None,
            auto_reduce=False,
            theme_params=ThemeParamsSchema(),
            web_app_button="None",
        )

    except Exception as e:
        api_logger.error(
            f"bot_id={bot_id}: Error while execute get_bot db_method with bot_id={bot_id}",
            extra=extra_params(bot_id=bot_id),
            exc_info=e,
        )
        raise HTTPInternalError


class APIOrderOption(BaseModel):
    option: OrderOptionSchema
    variants: list[OrderChooseOptionSchema] | None = None


@router.get("/get_order_options/{bot_id}/")
async def get_order_options_api(bot_id: int) -> list[APIOrderOption]:
    """
    :returns: list of Pydantic APIOrderOption Model with order option

    :raises HTTPBotNotFoundError:
    :raises HTTPInternalError:
    """
    try:
        bot = await bot_db.get_bot(bot_id)
        order_options = await order_option_db.get_all_order_options(bot.bot_id)

        api_res = []

        for option in order_options:
            if option.option_type == OrderOptionTypeValues.CHOOSE:
                variants = await order_choose_option_db.get_all_choose_options(option.id)
            else:
                variants = None
            api_res.append(APIOrderOption(option=option, variants=variants))

        return api_res

    except BotNotFoundError as e:
        api_logger.error(
            f"bot_id={bot_id}: bot_id={bot_id} is not found in database", extra=extra_params(bot_id=bot_id), exc_info=e
        )
        raise HTTPBotNotFoundError(bot_id=bot_id)


class HexColorData(BaseModel):
    color: str
    query_id: str


@router.post("/send_hex_color_to_bot")
async def send_hex_color_to_bot_api(data: HexColorData) -> str:
    """
    :raises HTTPInternalError:
    """
    try:
        api_logger.debug(f"get new hex data from web_app : {data}")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"http://"
                f"{custom_telegram_bot_settings.WEBHOOK_LOCAL_API_URL_HOST}:"
                f"{custom_telegram_bot_settings.WEBHOOK_LOCAL_API_PORT}"
                f"/send_hex_color_to_bot",
                data=data.model_dump_json(),
            ) as response:
                if response.status != 200:
                    api_logger.error(
                        f"Local API returned {response.status} status code " f"with text {await response.text()}"
                    )
                    raise LocalAPIException
    except LocalAPIException:
        raise HTTPInternalError(detail_message="Local Api error")
    except Exception as e:
        api_logger.error(f"Error while execute send_hex_color_to_bot api with data={data}", exc_info=e)
        raise HTTPInternalError

    return "success"
