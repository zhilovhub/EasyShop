import hashlib
import hmac
import json
import time
from operator import itemgetter
from urllib.parse import unquote, parse_qsl

from fastapi import HTTPException

from common_utils.env_config import API_DEBUG_MODE, TELEGRAM_TOKEN

from database.config import bot_db
from database.models.bot_model import BotNotFoundError


async def check_admin_authorization(bot_id: int, data_string: str) -> bool:
    if API_DEBUG_MODE and data_string == "DEBUG":
        return True
    if data_string:
        try:
            parsed_data = dict(parse_qsl(unquote(data_string), strict_parsing=True))
        except ValueError:
            raise HTTPException(status_code=401, detail="Unauthorized. initData not valid.")

        if "hash" not in parsed_data:
            raise HTTPException(status_code=401, detail="Unauthorized. 'hash' is not provided in data.")

        try:
            bot = await bot_db.get_bot(bot_id)
        except BotNotFoundError:
            raise HTTPException(status_code=404, detail=f"Bot with provided id ({bot_id}) not found in database.")

        if bot.created_by != json.loads(parsed_data['user'])['id']:
            raise HTTPException(status_code=401, detail=f"Unauthorized. You dont have access to bot with provided id.")

        if int(parsed_data['auth_date']) + 60 * 60 < time.time():
            raise HTTPException(status_code=401, detail=f"Unauthorized. Auth date is older than hour.")

        data_hash = parsed_data.pop('hash')

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
        )
        secret_key = hmac.new(
            key=b"WebAppData", msg=TELEGRAM_TOKEN.encode(), digestmod=hashlib.sha256
        )
        calculated_hash = hmac.new(
            key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256
        ).hexdigest()
        if calculated_hash == data_hash:
            return True
    raise HTTPException(status_code=401, detail="Unauthorized for that API method")
