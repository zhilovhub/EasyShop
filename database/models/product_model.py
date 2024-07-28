from typing import Optional, Annotated

from pydantic import BaseModel, Field, validate_call, ConfigDict, model_validator

from sqlalchemy import BigInteger, Column, String, ForeignKey, Integer, JSON
from sqlalchemy import select, insert, delete, update, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import insert as upsert

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot
from database.exceptions.exceptions import KwargsException

from logs.config import extra_params

from enum import Enum


class SameArticleProductError(KwargsException):
    """Raised when bot_id already has this article"""


class ProductNotFoundError(KwargsException):
    """Raised when provided product not found in database"""


class FilterNotFoundError(Exception):
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
        """
        :raises FilterNotFoundError:
        """
        if self.is_category_filter:
            pass
            # cats = await category_db.get_all_categories(self.bot_id)
            # for cat in cats:
            #     if cat.name.lower() == self.filter_name.lower():
            #         break
            # else:
            #     raise CategoryFilterNotFound(self.filter_name)
        elif self.filter_name.lower() not in PRODUCT_FILTERS:
            raise FilterNotFoundError(self.filter_name)
        return self


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), nullable=False)

    name = Column(String(100), nullable=False)  # TODO add test for unique name
    category = Column(ARRAY(BigInteger))
    description = Column(String(255), nullable=False)
    article = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    count = Column(BigInteger, nullable=False, default=0)
    picture = Column(ARRAY(String))
    extra_options = Column(JSON, default='[]')


class ExtraOptionType(str, Enum):
    TEXT = 'text'
    BLOCK = 'block'
    PRICED_BLOCK = "priced_block"


class ProductExtraOption(BaseModel):
    name: str
    type: ExtraOptionType
    variants: list[str]
    variants_prices: Optional[list[int]] = None  # not None if PRICED_BLOCK


class ProductWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)

    name: str = Field(max_length=100)
    category: list[int] | None = None
    description: str = Field(max_length=255)
    article: str = Field(frozen=True)
    price: int
    count: int
    picture: Optional[list[str] | None] = None
    extra_options: Optional[list[ProductExtraOption]] = []


class ProductSchema(ProductWithoutId):
    id: int

    def convert_to_notification_text(self, count: int, used_extra_options: list = None) -> str:
        """
        Converts ProductSchema to text for notification
        """
        if used_extra_options:
            options_text = ""
            for option in used_extra_options:
                options_text += f"\n • <i>{option.name}</i> : <u>{option.selected_variant}</u>"
                if option.price:
                    option_price = option.price - self.price
                    if option_price <= 0:
                        option_price_text = f"{option_price}"
                    else:
                        option_price_text = f"+{option_price}"
                    options_text += f" ({option_price_text}₽)"
                options_text += '\n'
            return f"<b>{self.name} {self.price}₽ x {count}шт</b> {options_text}"
        return f"<b>{self.name} {self.price}₽ x {count}шт</b>"


class NotEnoughProductsInStockToReduce(Exception):  # TODO Arsen should delete
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
        """
        :param bot_id: id of the Bot
        :param price_min: considers the products with price more than it
        :param price_max: considers the products with price less than it
        :param filters: a list of different ProductFilter to apply
        """
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
        """
        :raises ProductNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Product).where(Product.id == product_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            self.logger.debug(f"product with id {product_id} not found ")
            raise ProductNotFoundError(product_id=product_id)

        res = ProductSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}: found product {res}",
            extra=extra_params(product_id=res.id, bot_id=res.bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_product_by_bot_id_and_article(self, bot_id: int, article: str) -> ProductSchema:
        """
        :raises ProductNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Product).where(Product.bot_id == bot_id, Product.article == article))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            self.logger.debug(f"product with bot_id {bot_id} and article {article} not found.")
            raise ProductNotFoundError(bot_id=bot_id, article=article)

        res = ProductSchema.model_validate(raw_res)

        self.logger.debug(
            f"bot_id={res.bot_id}, article={res.article}: found product {res}",
            extra=extra_params(product_id=res.id, bot_id=res.bot_id, article=res.article)
        )

        return res

    async def check_article_in_bot_id(self, article: str, bot_id: int) -> bool:
        """
        Helps to consider only unique articles

        :return: True if the article already exists in bot else False
        """
        try:
            await self.get_product_by_bot_id_and_article(bot_id, article)
            return True
        except ProductNotFoundError:
            return False

    @validate_call(validate_return=True)
    async def add_product(self, new_product: ProductWithoutId) -> int:
        """
        :raises SameArticleProductError: when there is an attempt to add the duplicate article
        :raises IntegrityError:
        """
        status = await self.check_article_in_bot_id(new_product.article, new_product.bot_id)
        if status is True:
            raise SameArticleProductError(bot_id=new_product.bot_id, article=new_product.article)
        async with self.engine.begin() as conn:
            product_id = (await conn.execute(insert(Product).values(new_product.model_dump()))).inserted_primary_key[0]

        self.logger.debug(
            f"bot_id={new_product.bot_id}: added product {product_id} {new_product}",
            extra=extra_params(product_id=product_id, bot_id=new_product.bot_id)
        )

        return product_id

    @validate_call(validate_return=True)
    async def upsert_product(self, new_product: ProductWithoutId,
                             replace_duplicates: bool = False) -> int:  # TODO write tests for it
        """
        Inserts product if it doesn't exist otherwise update

        :raises IntegrityError:
        """
        new_product_dict = new_product.model_dump(exclude={"id"})
        async with self.engine.begin() as conn:
            if replace_duplicates:
                upsert_query = upsert(Product).values(new_product_dict).on_conflict_do_update(
                    constraint=f"products_pkey",
                    set_=new_product_dict
                )
                product_id = (await conn.execute(upsert_query)).inserted_primary_key[0]
                self.logger.debug(
                    f"bot_id={new_product.bot_id}: upserted product {product_id} {new_product}",
                    extra=extra_params(product_id=product_id, bot_id=new_product.bot_id)
                )
            else:
                upsert_query = upsert(Product).values(new_product_dict).on_conflict_do_nothing(
                    constraint=f"products_pkey",
                )
                product_id = (await conn.execute(upsert_query)).inserted_primary_key[0]
                self.logger.debug(
                    f"bot_id={new_product.bot_id}: upserted product {product_id} {new_product}",
                    extra=extra_params(product_id=product_id, bot_id=new_product.bot_id)
                )

        return product_id

    @validate_call(validate_return=True)
    async def update_product(self, updated_product: ProductSchema, exclude_pictures: bool = False) -> None:
        """
        :param updated_product: Product Schema to update
        :param exclude_pictures: True when we edit the product from frontend and we don't want to change the pictures
        because we have another logic with pictures
        """
        if exclude_pictures:
            updated_product_dump = updated_product.model_dump(exclude={"picture"})
        else:
            updated_product_dump = updated_product.model_dump()

        await self.get_product(updated_product.id)
        async with self.engine.begin() as conn:
            await conn.execute(
                update(Product).where(Product.id == updated_product.id).values(updated_product_dump)
            )

        self.logger.debug(
            f"bot_id={updated_product.bot_id}: updated product {updated_product}",
            extra=extra_params(product_id=updated_product.id, bot_id=updated_product.bot_id)
        )

    @validate_call(validate_return=True)
    async def delete_product(self, product_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Product).where(Product.id == product_id))

        self.logger.debug(
            f"product_id={product_id}: deleted product {product_id}",
            extra=extra_params(product_id=product_id)
        )

    @validate_call(validate_return=True)
    async def delete_all_products(self, bot_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Product).where(Product.bot_id == bot_id))

        self.logger.debug(
            f"bot_id={bot_id}: all products are deleted",
            extra=extra_params(bot_id=bot_id)
        )
