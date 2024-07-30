import aiohttp

from logs.config import api_logger, extra_params

from fastapi import APIRouter

from pydantic import BaseModel

from database.config import bot_db
from database.models.bot_model import BotNotFoundError

from api.utils import HTTPBotNotFoundError, HTTPInternalError, RESPONSES_DICT

from common_utils.exceptions.local_api_exceptions import LocalAPIException
from common_utils.env_config import LOCAL_API_SERVER_HOST, LOCAL_API_SERVER_PORT


PATH = "/api/settings"
router = APIRouter(
    prefix=PATH,
    tags=["settings"],
    responses=RESPONSES_DICT,
)


class WebAppOptions(BaseModel):  # TODO remove after Arsen has finished his task with Custom Bot Options
    bg_color: str | None


@router.get("/get_web_app_options/{bot_id}/")
async def get_web_app_options_api(bot_id: int) -> WebAppOptions:
    """
    :returns: Pydantic WebAppOptions Model with options

    :raises HTTPBotNotFoundError:
    :raises HTTPInternalError:
    """
    try:
        bot = await bot_db.get_bot(bot_id)

        if not bot.settings or "bg_color" not in bot.settings:
            options = WebAppOptions(bg_color=None)
            return options

        return WebAppOptions(bg_color=bot.settings['bg_color'])

    except BotNotFoundError as e:
        api_logger.error(
            f"bot_id={bot_id}: bot_id={bot_id} is not found in database",
            extra=extra_params(bot_id=bot_id),
            exc_info=e
        )
        raise HTTPBotNotFoundError(bot_id=bot_id)

    except Exception as e:
        api_logger.error(
            f"bot_id={bot_id}: Error while execute get_bot db_method with bot_id={bot_id}",
            extra=extra_params(bot_id=bot_id),
            exc_info=e
        )
        raise HTTPInternalError


class HexColorData(BaseModel):
    color: str
    query_id: str


@router.post("/send_hex_color_to_bot")
async def send_order_data_to_bot_api(data: HexColorData) -> str:
    """
    :raises HTTPInternalError:
    """
    try:
        api_logger.debug(f"get new hex data from web_app : {data}")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{LOCAL_API_SERVER_HOST}:{LOCAL_API_SERVER_PORT}"
                    f"/send_hex_color_to_bot",
                    data=data.json()
            ) as response:
                if response.status != 200:
                    api_logger.error(f"Local API returned {response.status} status code "
                                     f"with text {await response.text()}")
                    raise LocalAPIException
    except LocalAPIException:
        raise HTTPInternalError(detail_message="Local Api error")
    except Exception as e:
        api_logger.error(
            f"Error while execute send_hex_color_to_bot api with data={data}",
            exc_info=e
        )
        raise HTTPInternalError

    return "success"

