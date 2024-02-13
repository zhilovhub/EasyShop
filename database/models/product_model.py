from typing import Optional

from sqlalchemy import BigInteger, Column, String, ForeignKey, Float
from sqlalchemy import select, insert, delete, and_
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
    price = Column(Float, nullable=False)
    picture = Column(String)


class ProductWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_token: str = Field(frozen=True, max_length=46, min_length=46)
    name: str = Field(max_length=55)
    description: str = Field(max_length=255)
    price: float
    picture: Optional[str | None]


class ProductSchema(ProductWithoutId):
    id: int


class ProductDao(Dao):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)

    @validate_call(validate_return=True)
    async def get_all_products(self, bot_token: str) -> list[ProductSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Product).where(Product.bot_token == bot_token))
        await self.engine.dispose()
        raw_res = raw_res.fetchall()
        res = []
        for product in raw_res:
            res.append(ProductSchema.model_validate(product))
        return res

    @validate_call(validate_return=True)
    async def get_product(self, bot_token: str, product_id: int) -> ProductSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Product).where(and_(Product.bot_token == bot_token,
                                                                    Product.id == product_id)))
        await self.engine.dispose()
        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ProductNotFound
        return ProductSchema.model_validate(raw_res)

    @validate_call
    async def add_product(self, new_order: ProductWithoutId):
        async with self.engine.begin() as conn:
            await conn.execute(insert(Product).values(new_order.model_dump()))

    @validate_call
    async def delete_product(self, product_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Product).where(Product.id == product_id))
