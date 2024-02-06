from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.types import TypeDecorator, Unicode
from sqlalchemy import Table, Column, LargeBinary, String, ForeignKey, BigInteger, DateTime
from sqlalchemy import MetaData, Dialect

from enums import ProductStatusValues


class ProductStatus(TypeDecorator):
    impl = Unicode
    cache_ok = True

    def process_bind_param(self, value: Optional[ProductStatusValues], dialect: Dialect) -> String:
        return value.value

    def process_result_value(self, value: Optional[String], dialect: Dialect) -> Optional[ProductStatusValues]:
        match value:
            case ProductStatusValues.BACKLOG.value:
                return ProductStatusValues.BACKLOG
            case ProductStatusValues.CANCELLED.value:
                return ProductStatusValues.CANCELLED
            case ProductStatusValues.PROCESSING.value:
                return ProductStatusValues.PROCESSING
            case ProductStatusValues.FINISHED.value:
                return ProductStatusValues.FINISHED


class UserStatus(TypeDecorator):
    impl = Unicode
    cache_ok = True

    def process_bind_param(self, value: Optional[ProductStatusValues], dialect: Dialect) -> String:
        return value.value

    def process_result_value(self, value: Optional[String], dialect: Dialect) -> Optional[ProductStatusValues]:
        match value:
            case ProductStatusValues.BACKLOG.value:
                return ProductStatusValues.BACKLOG
            case ProductStatusValues.CANCELLED.value:
                return ProductStatusValues.CANCELLED
            case ProductStatusValues.PROCESSING.value:
                return ProductStatusValues.PROCESSING
            case ProductStatusValues.FINISHED.value:
                return ProductStatusValues.FINISHED


# TODO add logs
class AlchemyDB:
    def __init__(self, alchemy_url: str):
        self.metadata = MetaData()
        self.products = Table("products", self.metadata,
                              Column("id", BigInteger, primary_key=True),
                              Column("name", String(55)),
                              Column("price", BigInteger),
                              Column("picture", LargeBinary),
                              )
        self.users = Table("custom_bot_users", self.metadata,
                           Column("user_id", BigInteger, primary_key=True),
                           Column("status", String(55))
                           )
        self.orders = Table("orders", self.metadata,
                              Column("id", BigInteger, primary_key=True),
                              Column("product_id", ForeignKey("products.id")),
                              Column("from_user", ForeignKey("custom_bot_users.user_id")),
                              Column("date", DateTime),
                              Column("address", String),
                              Column("status", ProductStatus)
                              )

        self.engine = create_async_engine(alchemy_url)

    async def connect(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(self.metadata.create_all)
        await self.engine.dispose()
