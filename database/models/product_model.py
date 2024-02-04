from typing import Optional

from sqlalchemy import BigInteger, Column, String, LargeBinary
from sqlalchemy.ext.asyncio import AsyncEngine

from pydantic import BaseModel, Field

from database.models import Base
from database.models.dao import Dao


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True)
    name = Column(String(55), nullable=False)
    price = Column(BigInteger, nullable=False)
    picture = Column(LargeBinary)


class ProductSchema(BaseModel):
    id: int
    name: str = Field(max_length=55)
    price: int
    picture: Optional[bytes|None]


class ProductDao(Dao):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)
