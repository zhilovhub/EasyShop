from typing import Optional, Annotated

from pydantic import BaseModel, Field, validate_call, ConfigDict, model_validator

from sqlalchemy import BigInteger, Column, String, ForeignKey, Integer, JSON
from sqlalchemy import select, insert, delete, update, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import insert as upsert

from bot.exceptions import InvalidParameterFormat

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot

from logs.config import extra_params

from enum import Enum


class ProductNotFound(Exception):
    """Raised when provided product not found in database"""
    pass


class FilterNotFound(Exception):
    """Raised when filter name provided to ProductFilter class is not a valid filter name from filters list"""

    def __init__(self, filter_name: str, message: str = "Provided filter name ('{FILTER_NAME}') not found"):
        self.filter_name = filter_name
        self.message = message.replace("{FILTER_NAME}", filter_name.lower())
        super().__init__(self.message)


PRODUCT_FILTERS = {"rating": "По рейтингу",
                   "popular": "По популярности",
                   "price": "По цене",
                   "search": "По поиску"}


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

    name = Column(String(100), unique=True, nullable=False)  # TODO add test for unique name
    category = Column(ARRAY(BigInteger))
    description = Column(String(255), nullable=False)
    article = Column(String)
    price = Column(Integer, nullable=False)
    count = Column(BigInteger, nullable=False, default=0)
    picture = Column(ARRAY(String))
    extra_options = Column(JSON)


class ExtraOptionType(str, Enum):
    TEXT = 'text'
    BLOCK = 'block'
    PRICED_BLOCK = "priced_block"


class ProductExtraOption(BaseModel):
    name: str
    type: ExtraOptionType
    variants: list[str]
    variants_prices: list[int]


class ProductWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)

    name: str = Field(max_length=100)
    category: list[int] | None = None
    description: str = Field(max_length=255)
    article: Optional[str | None] = None
    price: int
    count: int
    picture: Optional[list[str] | None] = None
    extra_options: Optional[list[ProductExtraOption] | None] = None


class ProductSchema(ProductWithoutId):
    id: int

    def convert_to_notification_text(self, count: int, used_extra_options: list = None) -> str:
        if used_extra_options:
            options_text = ""
            for option in used_extra_options:
                options_text += f"\n • <i>{option.name}</i> : <u>{option.selected_variant}</u>"
                if option.price:
                    options_text += f" ({option.price}₽)"
                options_text += '\n'
            return f"<b>{self.name} {self.price}₽ {options_text}\nx {count}шт</b>"
        return f"<b>{self.name} {self.price}₽ x {count}шт</b>"


class NotEnoughProductsInStockToReduce(Exception):
    """Raised when auto_reduce on order option is enabled and product reduce amount is more than product count"""

    def __init__(self, product: ProductSchema, amount: int,
                 message: str = "Product with name ('{PRODUCT_NAME}') and id ({PRODUCT_ID}) has not enough items "
                                "in stock (need: {ITEMS_NEED}, stock: {ITEMS_STOCK})"):

        self.product = product
        self.message = message.replace("{PRODUCT_NAME}", product.name.lower()).replace(
            "{PRODUCT_ID}", str(product.id)
        ).replace(
            "{ITEMS_NEED}", str(amount)
        ).replace(
            "{ITEMS_STOCK}", str(product.count)
        )
        super().__init__(self.message)


class ProductDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_products(
            self,
            bot_id: int,
            price_min: int = 0,
            price_max: int = 2147483647,
            filters: list[ProductFilter] | None = None
    ) -> list[ProductSchema]:
        sql_select = select(Product).where(
            and_(and_(Product.bot_id == bot_id, Product.price >= price_min), Product.price <= price_max)
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
                            sql_select = sql_select.filter(
                                Product.name.ilike('%' + product_filter.search_word.lower() + '%'))
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

        self.logger.debug(
            f"bot_id={bot_id}: has {len(res)} products",
            extra=extra_params(bot_id=bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_product(self, product_id: int) -> ProductSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Product).where(Product.id == product_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise ProductNotFound

        res = ProductSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: product {res.id} is found",
            extra=extra_params(product_id=res.id, bot_id=res.bot_id)
        )

        return res

    @validate_call
    async def add_product(self, new_product: ProductWithoutId) -> int:
        if type(new_product) != ProductWithoutId:
            raise InvalidParameterFormat("new_product must be type of ProductWithoutId")

        async with self.engine.begin() as conn:
            product_id = (await conn.execute(insert(Product).values(new_product.model_dump()))).inserted_primary_key[0]

        self.logger.debug(
            f"bot_id={new_product.bot_id}: product {product_id} is added",
            extra=extra_params(product_id=product_id, bot_id=new_product.bot_id)
        )

        return product_id

    @validate_call
    async def upsert_product(self, new_product: ProductWithoutId,
                             replace_duplicates: bool = False) -> int:  # TODO write tests for it
        if type(new_product) not in (ProductWithoutId, ProductSchema):
            raise InvalidParameterFormat("new_product must be a subclass of ProductWithoutId")

        new_product_dict = new_product.model_dump(exclude={"id"})
        async with self.engine.begin() as conn:
            if replace_duplicates:
                upsert_query = upsert(Product).values(new_product_dict).on_conflict_do_update(
                    constraint=f"products_name_key",
                    set_=new_product_dict
                )
                product_id = (await conn.execute(upsert_query)).inserted_primary_key[0]
                self.logger.debug(
                    f"bot_id={new_product.bot_id}: product {product_id} is upserted",
                    extra=extra_params(product_id=product_id, bot_id=new_product.bot_id)
                )
            else:
                upsert(Product).values(new_product_dict).on_conflict_do_nothing(
                    constraint=f"products_name_key",
                )  # TODO что-то тут странное. Почему запрос есть, но не исполняется?
                product_id = -1

        return product_id

    @validate_call
    async def update_product(self, updated_product: ProductSchema):
        await self.get_product(updated_product.id)
        async with self.engine.begin() as conn:
            await conn.execute(
                update(Product).where(Product.id == updated_product.id).values(updated_product.model_dump())
            )

        self.logger.debug(
            f"bot_id={updated_product.bot_id}: product {updated_product.id} is updated",
            extra=extra_params(product_id=updated_product.id, bot_id=updated_product.bot_id)
        )

    @validate_call
    async def delete_product(self, product_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Product).where(Product.id == product_id))

        self.logger.debug(
            f"product_id={product_id}: product {product_id} is deleted",
            extra=extra_params(product_id=product_id)
        )

    @validate_call
    async def delete_all_products(self, bot_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Product).where(Product.bot_id == bot_id))

        self.logger.debug(
            f"bot_id={bot_id}: all products are deleted",
            extra=extra_params(bot_id=bot_id)
        )
