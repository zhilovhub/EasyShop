import aiohttp

from common_utils.config import custom_telegram_bot_settings
from common_utils.exceptions.local_api_exceptions import LocalAPIException

from database.config import bot_db


async def start_custom_bot(bot_id: int) -> None:
    """
    Is used to send start bot request to local multibot server

    :raises LocalAPIException:
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"http://"
                f"{custom_telegram_bot_settings.WEBHOOK_LOCAL_API_URL_HOST}"
                f":{custom_telegram_bot_settings.WEBHOOK_LOCAL_API_PORT}/start_bot/{bot_id}"
        ) as response:
            user_bot = await bot_db.get_bot(bot_id)
            user_bot.status = "online"
            await bot_db.update_bot(user_bot)
            if response.status != 200:
                raise LocalAPIException(f"Local API returned {response.status} status code "
                                        f"with text {await response.text()}")


async def stop_custom_bot(bot_id: int) -> None:
    """
    Is used to send stop bot request to local multibot server

    :raises LocalAPIException:
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"http://"
                f"{custom_telegram_bot_settings.WEBHOOK_LOCAL_API_URL_HOST}:"
                f"{custom_telegram_bot_settings.WEBHOOK_LOCAL_API_PORT}/stop_bot/{bot_id}"
        ) as response:
            user_bot = await bot_db.get_bot(bot_id)
            user_bot.status = "offline"
            await bot_db.update_bot(user_bot)
            if response.status != 200:
                raise LocalAPIException(f"Local API returned {response.status} status code "
                                        f"with text {await response.text()}")
