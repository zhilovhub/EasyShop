from pydantic import validate_call

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine


class Dao:
    """
    The main class for all Tables' dao
    """

    def __init__(self, engine: AsyncEngine, logger) -> None:
        self.engine = engine
        self.logger = logger

    @validate_call(validate_return=True)
    async def clear_table(self, table) -> None:
        """
        Often used in tests
        :param table: an object with Base type
        """
        async with self.engine.begin() as conn:
            await conn.execute(delete(table))
        await self.engine.dispose()

        self.logger.debug(f"Table {table.__tablename__} has been cleared")
