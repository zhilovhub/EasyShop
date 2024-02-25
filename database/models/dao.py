from sqlalchemy.ext.asyncio import AsyncEngine


class Dao:
    def __init__(self, engine: AsyncEngine, logger) -> None:
        self.engine = engine
        self.logger = logger
