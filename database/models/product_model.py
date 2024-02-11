from typing import Optional, Union

from sqlalchemy import BigInteger, Column, String, LargeBinary, ForeignKey
from sqlalchemy import select, update, insert, delete, and_
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field, field_validator, validate_call

from database.models import Base
from database.models.dao import Dao

from .custom_bot_model import CustomBotSchema, CustomBot


class ProductNotFound(Exception):
    """Raised when provided product not found in database"""
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True)
    bot_token = Column(ForeignKey(CustomBot.bot_token), nullable=False)
    name = Column(String(55), nullable=False)
    description = Column(String(255), nullable=False)
    price = Column(BigInteger, nullable=False)
    picture = Column(LargeBinary)


class ProductWithoutId(BaseModel):
    bot_token: str = Field(frozen=True, max_length=46, min_length=46)
    name: str = Field(max_length=55)
    description: str = Field(max_length=255)
    price: float
    picture: Optional[bytes | None]


class ProductSchema(ProductWithoutId):
    id: int


class ProductDao(Dao):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)

    @validate_call
    async def get_all_products(self, bot_token: str) -> list[ProductSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Product).where(Product.bot_token == bot_token))
        await self.engine.dispose()
        raw_res = raw_res.fetchall()
        res = []
        for product in raw_res:
            res.append(ProductSchema.model_validate(product))
        return res

    @validate_call
    async def get_product(self, bot_token: str, product_id: int) -> ProductSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Product).where(and_(Product.bot_token == bot_token,
                                                                    Product.id == product_id)))
        await self.engine.dispose()
        raw_res = raw_res.fetchall()
        if not raw_res:
            raise ProductNotFound
        res = ProductSchema.model_validate(raw_res)
        return res

    @validate_call
    async def add_product(self, new_order: ProductWithoutId):
        async with self.engine.begin() as conn:
            await conn.execute(insert(Product).values(new_order.model_dump()))
