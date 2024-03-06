import aiohttp

from bot import config
from bot.exceptions import LocalAPIException


async def start_custom_bot(bot_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"http://{config.LOCAL_API_SERVER_HOST}:{config.LOCAL_API_SERVER_PORT}/start_bot/{bot_id}") as response:
            if response.status != 200:
                raise LocalAPIException(f"API returned {response.status} status code "
                                        f"with text {await response.text()}")


async def stop_custom_bot(bot_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"http://{config.LOCAL_API_SERVER_HOST}:{config.LOCAL_API_SERVER_PORT}/stop_bot/{bot_id}") as response:
            if response.status != 200:
                raise LocalAPIException(f"API returned {response.status} status code "
                                        f"with text {await response.text()}")
