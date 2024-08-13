import asyncio

from database.models.models import Database
from sqlalchemy import text

from logs.config import db_logger


database: Database = Database(sqlalchemy_url="", logger=db_logger)


async def main() -> None:
    async with database.engine.begin() as conn:
        await conn.execute(text("DROP TABLE alembic_version"))

    await database.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
