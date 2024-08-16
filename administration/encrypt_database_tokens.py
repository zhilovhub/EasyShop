import asyncio

from database.models.models import Database
from database.models.bot_model import BotDao

from logs.config import db_logger


database: Database = Database(sqlalchemy_url="", logger=db_logger, unique_id="util")
db_bot: BotDao = database.get_bot_dao()


async def main() -> None:  # modify process_result_value in DatabaseBotTokenEncryptor before launching
    all_bots = await db_bot.get_bots()

    for bot in all_bots:
        await db_bot.update_bot(bot)


if __name__ == "__main__":
    asyncio.run(main())
