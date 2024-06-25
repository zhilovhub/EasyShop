import time
from functools import wraps
from api.loader import db_engine, DEBUG, MAIN_BOT_TOKEN
from database.models.bot_model import BotDao, BotNotFound
from fastapi import HTTPException
from aiogram.utils.web_app import WebAppInitData
from urllib.parse import unquote, quote, parse_qsl
import hmac
import hashlib
import base64
from operator import itemgetter
from typing import *
import json


bot_db: BotDao = db_engine.get_bot_dao()


async def check_admin_authorization(bot_id: int, data_string: str) -> bool:
    if data_string:
        if DEBUG and data_string == "DEBUG":
            return True
        try:
            parsed_data = dict(parse_qsl(unquote(data_string), strict_parsing=True))
        except ValueError:
            raise HTTPException(status_code=401, detail="Unauthorized. initData not valid.")

        if "hash" not in parsed_data:
            raise HTTPException(status_code=401, detail="Unauthorized. 'hash' is not provided in data.")

        try:
            bot = await bot_db.get_bot(bot_id)
        except BotNotFound:
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
            key=b"WebAppData", msg=MAIN_BOT_TOKEN.encode(), digestmod=hashlib.sha256
        )
        calculated_hash = hmac.new(
            key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256
        ).hexdigest()
        if calculated_hash == data_hash:
            return True
    raise HTTPException(status_code=401, detail="Unauthorized for that API method")


# def check_admin_headers_auth(func):
#     @wraps(func)
#     def wrapper(request, *args, **kwargs):
#         print(*args)
#         print(**kwargs)
#         # if request.headers.get("SECRET", None) != SECRET_KEY:
#         #     raise HTTPException(status_code=401, detail="Invalid client secret")
#         return func(request, *args, **kwargs)
#     return wrapper
#
#
# def auth_required(func):
#     @wraps(func)
#     async def wrapper(request, *args, **kwargs):
#         await check_admin_authorization(bot_id=0,
#                                         data_string=request.headers.get("authorization-data", None),
#                                         data_hash=request.headers.get("authorization-data", None))
#         print(args)
#         print(kwargs)
#         return await func(request, *args, **kwargs)
#
#     return wrapper
