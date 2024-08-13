import hashlib
import hmac
import json
import time
from operator import itemgetter
from urllib.parse import unquote, parse_qsl

from api.utils.exceptions import HTTPUnauthorizedError, HTTPBotNotFoundError

from common_utils.config import api_settings, main_telegram_bot_settings

from database.config import bot_db
from database.models.bot_model import BotNotFoundError


async def check_admin_authorization(bot_id: int, data_string: str, custom_bot_validate: bool = False) -> bool:
    """
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

    :param bot_id: custom bot id
    :param data_string: initData from telegram WebApp
    :param custom_bot_validate: True if validate is need with custom bot token except of main bot token (default: False)

    :returns: True if (hash from telegram is valid) or the (mode is DEBUG and data_string is "DEBUG") else False

    :raises HTTPUnauthorizedError:
    :raises HTTPBotNotFoundError:
    """
    if api_settings.API_DEBUG_MODE and data_string == "DEBUG":
        return True
    if data_string:
        try:
            parsed_data = dict(parse_qsl(unquote(data_string), strict_parsing=True))
        except ValueError:
            raise HTTPUnauthorizedError(detail_message="Unauthorized. initData not valid.")

        if "hash" not in parsed_data:
            raise HTTPUnauthorizedError(detail_message="Unauthorized. 'hash' is not provided in data.")

        try:
            bot = await bot_db.get_bot(bot_id)
        except BotNotFoundError:
            raise HTTPBotNotFoundError(bot_id=bot_id)

        if not custom_bot_validate and bot.created_by != json.loads(parsed_data["user"])["id"]:
            raise HTTPUnauthorizedError(detail_message="Unauthorized. You dont have access to bot with provided id.")

        if int(parsed_data["auth_date"]) + 60 * 60 < time.time():
            raise HTTPUnauthorizedError(detail_message="Unauthorized. Auth date is older than hour.")

        data_hash = parsed_data.pop("hash")

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0)))

        if not custom_bot_validate:
            secret_key = hmac.new(
                key=b"WebAppData", msg=main_telegram_bot_settings.TELEGRAM_TOKEN.encode(), digestmod=hashlib.sha256
            )
        else:
            secret_key = hmac.new(key=b"WebAppData", msg=bot.token.encode(), digestmod=hashlib.sha256)

        calculated_hash = hmac.new(
            key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256
        ).hexdigest()
        if calculated_hash == data_hash:
            return True
    raise HTTPUnauthorizedError(detail_message="Unauthorized for that API method")
