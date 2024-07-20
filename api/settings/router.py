from logs.config import api_logger, extra_params

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from database.config import bot_db
from database.models.bot_model import BotNotFound


PATH = "/api/settings"
router = APIRouter(
    prefix=PATH,
    tags=["settings"],
    responses={404: {"description": "Setting not found"}},
)


class WebAppOptions(BaseModel):
    bg_color: str


@router.get("/get_web_app_options/{bot_id}/")
async def get_product_api(bot_id: int) -> WebAppOptions:
    try:
        bot = await bot_db.get_bot(bot_id)

        if not bot.settings or "bg_color" not in bot.settings:
            options = WebAppOptions(bg_color="telegram")
            return options

        return WebAppOptions(bg_color=bot.settings['bg_color'])

    except BotNotFound as e:
        api_logger.error(
            f"bot_id={bot_id}: bot_id={bot_id} is not found in database",
            extra=extra_params(bot_id=bot_id),
            exc_info=e
        )
        raise HTTPException(status_code=404, detail="Bot not found.")

    except Exception as e:
        api_logger.error(
            f"bot_id={bot_id}: Error while execute get_bot db_method with bot_id={bot_id}",
            extra=extra_params(bot_id=bot_id),
            exc_info=e
        )
        raise HTTPException(status_code=500, detail="Internal error.")
