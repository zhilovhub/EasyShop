from sqlalchemy.ext.asyncio import AsyncEngine


class Dao:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
