from typing import Optional

from sqlalchemy import BigInteger, Column, String, ForeignKey, Integer
from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, validate_call, ConfigDict

from database.models import Base
from database.models.dao import Dao

from .bot_model import Bot


class ProductNotFound(Exception):
    """Raised when provided product not found in database"""
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True)
    bot_token = Column(ForeignKey(Bot.bot_token, ondelete="CASCADE"), nullable=False)
    name = Column(String(55), nullable=False)
    description = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)
    picture = Column(String)


class ProductWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_token: str = Field(frozen=True, max_length=46, min_length=46)
    name: str = Field(max_length=55)
    description: str = Field(max_length=255)
    price: int
    picture: Optional[str | None]


class ProductSchema(ProductWithoutId):
    id: int

    def convert_to_notification_text(self) -> str:
        return f"<b>{self.name} {self.price}₽</b>"


class ProductDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_products(self, bot_token: str) -> list[ProductSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Product).where(Product.bot_token == bot_token))
        await self.engine.dispose()
        raw_res = raw_res.fetchall()
        res = []
        for product in raw_res:
            res.append(ProductSchema.model_validate(product))

        self.logger.info(f"get_all_products method with token: {bot_token} success.")
        return res

    @validate_call(validate_return=True)
    async def get_product(self, product_id: int) -> ProductSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Product).where(Product.id == product_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ProductNotFound

        self.logger.info(f"get_product method with product_id: {product_id} success.")
        return ProductSchema.model_validate(raw_res)

    @validate_call
    async def add_product(self, new_product: ProductWithoutId):
        async with self.engine.begin() as conn:
            await conn.execute(insert(Product).values(new_product.model_dump()))
        self.logger.info(f"successfully add product with id {new_product.id} to db.")

    @validate_call
    async def update_product(self, updated_product: ProductSchema):
        await self.get_product(updated_product.id)
        async with self.engine.begin() as conn:
            await conn.execute(update(Product).where(Product.id == updated_product.id).values(updated_product.model_dump()))
        self.logger.info(f"successfully update product with id {updated_product.id} at db.")

    @validate_call
    async def delete_product(self, product_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Product).where(Product.id == product_id))
        self.logger.info(f"deleted product with id {product_id}")
