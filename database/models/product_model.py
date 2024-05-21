from typing import Optional

from sqlalchemy import BigInteger, Column, String, ForeignKey, Integer, JSON
from sqlalchemy import select, insert, delete, update, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.dialects.postgresql import insert as upsert
from sqlalchemy.dialects.postgresql import ARRAY

from sqlalchemy_filters import apply_filters

from pydantic import BaseModel, Field, validate_call, ConfigDict, model_validator
from typing import Annotated, List

from bot.exceptions import InvalidParameterFormat

from database.models import Base
from database.models.dao import Dao

from .bot_model import Bot
from .category_model import Category


class ProductNotFound(Exception):
    """Raised when provided product not found in database"""
    pass


class FilterNotFound(Exception):
    """Raised when filter name provided to ProductFilter class is not a valid filter name from filters list"""

    def __init__(self, filter_name: str, message: str="Provided filter name ('{FILTER_NAME}') not found"):
        self.filter_name = filter_name
        self.message = message.replace("{FILTER_NAME}", filter_name.lower())
        super().__init__(self.message)


# class CategoryFilterNotFound(Exception):
#     """Raised when category name provided to ProductFilter class is not exist in categories table"""
#
#     def __init__(self, category_name: str, message: str = "Provided category name ('{CAT_NAME}') for category filter not found"):
#         self.category_name = category_name
#         self.message = message.replace("{{CAT_NAME}}", category_name.lower())
#         super().__init__(self.message)


PRODUCT_FILTERS = {"rating": "сортирует по рейтингу из отзывов",
                   "popular": "сортирует по частоте покупки",
                   "price": "сортирует по цене",
                   "search": "сортирует товары по совпадению с поисковым запросом"}


class ProductFilterWithoutBot(BaseModel):
    filter_name: Annotated[str, Field(validate_default=True)]
    is_category_filter: bool = False
    reverse_order: bool = False


class ProductFilter(ProductFilterWithoutBot):
    bot_id: int = Field(frozen=True)
    category_id: int | None
    search_word: str | None

    @model_validator(mode='after')
    def validate_filter_name(self):
        if self.is_category_filter:
            pass
            # cats = await category_db.get_all_categories(self.bot_id)
            # for cat in cats:
            #     if cat.name.lower() == self.filter_name.lower():
            #         break
            # else:
            #     raise CategoryFilterNotFound(self.filter_name)
        elif self.filter_name.lower() not in PRODUCT_FILTERS:
            raise FilterNotFound(self.filter_name)
        return self


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), nullable=False)

    name = Column(String(55), unique=True, nullable=False)  # TODO add test for unique name
    category = Column(ARRAY(BigInteger))
    description = Column(String(255), nullable=False)
    article = Column(String)
    price = Column(Integer, nullable=False)
    count = Column(BigInteger, nullable=False, default=0)
    picture = Column(String)
    extra_options = Column(JSON, default="{}")


class ProductWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)

    name: str = Field(max_length=55)
    category: list[int] | None
    description: str = Field(max_length=255)
    article: Optional[str | None]
    price: int
    count: int
    picture: Optional[str | None]
    extra_options: Optional[dict | None] = {}


class ProductSchema(ProductWithoutId):
    id: int

    def convert_to_notification_text(self, count: int, extra_options: dict) -> str:
        # if extra_options is not None:
        #     options = "\n" + "".join([f"{title} : {opt}" for title, opt in extra_options.items()]) + "\n"
        # else:
        #     options = ""
        # return f"<b>{self.name} <i>{options}</i> {self.price}₽ x {count}шт</b>"
        return f"<b>{self.name} {self.price}₽ x {count}шт</b>"


class ProductDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_products(self, bot_id: int, price_min: int = 0, price_max: int = 2147483647,
                               filters: list[ProductFilter] | None = None) -> list[ProductSchema]:
        sql_select = select(Product).where(and_(
                    and_(
                        Product.bot_id == bot_id, Product.price >= price_min)
                    , Product.price <= price_max)
                )

        if filters:
            for product_filter in filters:
                if product_filter.is_category_filter:
                    sql_select = sql_select.filter(Product.category.contains([product_filter.category_id]))
                else:
                    match product_filter.filter_name:
                        case "price":
                            if product_filter.reverse_order:
                                sql_select = sql_select.order_by(desc(Product.price))
                            else:
                                sql_select = sql_select.order_by(asc(Product.price))
                        case "search":
                            sql_select = sql_select.filter(Product.name.ilike('%' + product_filter.search_word.lower() + '%'))
                        case "rating":
                            pass
                        case "popular":
                            pass

        async with self.engine.begin() as conn:
            raw_res = await conn.execute(sql_select)
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for product in raw_res:
            res.append(ProductSchema.model_validate(product))

        self.logger.info(f"get_all_products method with bot_id: {bot_id} success.")
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
    async def add_product(self, new_product: ProductWithoutId) -> int:
        if type(new_product) != ProductWithoutId:
            raise InvalidParameterFormat("new_product must be type of ProductWithoutId")

        async with self.engine.begin() as conn:
            product_id = (await conn.execute(insert(Product).values(new_product.model_dump()))).inserted_primary_key[0]

        self.logger.info(f"successfully add product with id {product_id} to db")
        return product_id

    @validate_call
    async def upsert_product(self, new_product: ProductWithoutId) -> int:  # TODO write tests for it
        if type(new_product) not in (ProductWithoutId, ProductSchema):
            raise InvalidParameterFormat("new_product must be a subclass of ProductWithoutId")

        new_product_dict = new_product.model_dump(exclude={"id"})
        async with self.engine.begin() as conn:
            upsert_query = upsert(Product).values(new_product_dict).on_conflict_do_update(
                constraint=f"products_name_key",
                set_=new_product_dict
            )
            product_id = (await conn.execute(upsert_query)).inserted_primary_key[0]

        self.logger.info(f"successfully upserted product with id {product_id} to db")
        return product_id

    @validate_call
    async def update_product(self, updated_product: ProductSchema):
        await self.get_product(updated_product.id)
        async with self.engine.begin() as conn:
            await conn.execute(
                update(Product).where(Product.id == updated_product.id).values(updated_product.model_dump())
            )
        self.logger.info(f"successfully update product with id {updated_product.id} at db.")

    @validate_call
    async def delete_product(self, product_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Product).where(Product.id == product_id))
        self.logger.info(f"deleted product with id {product_id}")

    @validate_call
    async def delete_all_products(self, bot_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Product).where(Product.bot_id == bot_id))
        self.logger.info(f"deleted all products with bot_id {bot_id}")
