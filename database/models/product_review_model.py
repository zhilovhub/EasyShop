from pydantic import BaseModel, ConfigDict, Field, validate_call

from sqlalchemy import Column, BigInteger, String, select, ForeignKey, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot
from database.models.product_model import Product
from database.models.custom_bot_user_model import CustomBotUser

from logs.config import extra_params


class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(BigInteger, primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), nullable=False)
    product_id = Column(ForeignKey(Product.id, ondelete="CASCADE"), nullable=False)
    mark = Column(BigInteger, nullable=False)
    review_text = Column(String, nullable=True)
    user_id = Column(ForeignKey(CustomBotUser.user_id, ondelete="CASCADE"), nullable=False)


class ProductReviewSchemaWithoutID(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)
    product_id: int = Field(frozen=True)
    mark: int
    review_text: str | None = None
    user_id: int


class ProductReviewSchema(ProductReviewSchemaWithoutID):
    id: int = Field(frozen=True)


class ProductReviewDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_reviews_by_product_id(self, product_id: int) -> list[ProductReviewSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ProductReview).where(ProductReview.product_id == product_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for product in raw_res:
            res.append(ProductReviewSchema.model_validate(product))

        self.logger.debug(
            f"priduct_id={product_id}: has {len(res)} reviews",
            extra=extra_params(product_id=product_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_product_review_by_user_id_and_product_id(self, user_id: int, product_id: int) -> ProductReviewSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ProductReview).where(ProductReview.user_id == user_id, ProductReview.product_id == product_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()

        if res is not None:
            self.logger.debug(
                f"product_review with product_id={product_id} and user_id {user_id} is found",
                extra=extra_params(product_id=product_id, user_id=user_id)
            )

        return res

    @validate_call(validate_return=True)
    async def get_product_review(self, review_id: int) -> ProductReviewSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ProductReview).where(ProductReview.id == review_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()

        if res is not None:
            self.logger.debug(
                f"product_review_id={review_id}: review {review_id} is found",
                extra=extra_params(product_review_id=review_id)
            )

        return res

    @validate_call
    async def add_product_review(self, new_review: ProductReviewSchemaWithoutID) -> int:
        if type(new_review) != ProductReviewSchemaWithoutID:
            raise InvalidParameterFormat("new_review must be type of ProductReviewSchemaWithoutID")

        async with self.engine.begin() as conn:
            review_id = (await conn.execute(insert(ProductReview).values(new_review.model_dump()))).inserted_primary_key[0]

        self.logger.debug(
            f"product_review={review_id}: review {review_id} is added to database",
            extra=extra_params(product_review=review_id)
        )

        return review_id

    @validate_call
    async def update_product_review(self, updated_review: ProductReviewSchema) -> None:
        await self.get_product_review(updated_review.id)
        async with self.engine.begin() as conn:
            await conn.execute(
                update(ProductReview).where(ProductReview.id == updated_review.id).values(updated_review.model_dump())
            )

        self.logger.debug(
            f"product_review={updated_review.id}: review {updated_review.id} is updated",
            extra=extra_params(product_review=updated_review.id)
        )

    @validate_call
    async def delete_product_review(self, review_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(ProductReview).where(ProductReview.id == review_id))

        self.logger.debug(
            f"product_review={review_id}: review {review_id} is deleted",
            extra=extra_params(product_review=review_id)
        )
