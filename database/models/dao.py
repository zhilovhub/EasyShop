from sqlalchemy.ext.asyncio import AsyncEngine


class Dao:
    """
    The main class for all Tables' dao
    """

    def __init__(self, engine: AsyncEngine, logger) -> None:
        self.engine = engine
        self.logger = logger
