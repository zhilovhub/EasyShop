from pydantic import BaseModel, ConfigDict, Field, validate_call

from sqlalchemy import BOOLEAN, Column, BigInteger, String, select, ForeignKey, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot
from database.models.user_model import User
from database.models.product_model import Product
from database.exceptions.exceptions import KwargsException

from logs.config import extra_params


class ProductReviewNotFoundError(KwargsException):
    """Raised when provided product_review not found in database"""


class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(BigInteger, primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), nullable=False)
    product_id = Column(ForeignKey(Product.id, ondelete="CASCADE"), nullable=False)
    mark = Column(BigInteger, nullable=False)
    review_text = Column(String, nullable=True)
    user_id = Column(ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False)
    accepted = Column(BOOLEAN, default=False, nullable=False)


class ProductReviewSchemaWithoutID(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)
    product_id: int = Field(frozen=True)
    mark: int
    review_text: str | None = None
    user_id: int
    accepted: bool = False


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
            f"product_id={product_id}: has {len(res)} reviews",
            extra=extra_params(product_id=product_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_product_review_by_user_id_and_product_id(
            self,
            user_id: int,
            product_id: int
    ) -> ProductReviewSchema:
        """
        :raises ProductReviewNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ProductReview).where(ProductReview.user_id == user_id, ProductReview.product_id == product_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()
        if not res:
            raise ProductReviewNotFoundError(user_id=user_id, product_id=product_id)

        res = ProductReviewSchema.model_validate(res)

        if res is not None:
            self.logger.debug(
                f"product_id={product_id}, user_id {user_id}: found product_review {res}",
                extra=extra_params(product_id=product_id, user_id=user_id)
            )

        return res

    @validate_call(validate_return=True)
    async def get_product_review(self, review_id: int) -> ProductReviewSchema:
        """
        :raises ProductReviewNotFoundError:
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(ProductReview).where(ProductReview.id == review_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()
        if not res:
            raise ProductReviewNotFoundError(review_id=review_id)

        res = ProductReviewSchema.model_validate(res)

        self.logger.debug(
            f"product_review_id={review_id}: found product_review {review_id}",
            extra=extra_params(product_review_id=review_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_product_review(self, new_review: ProductReviewSchemaWithoutID) -> int:
        """
        :raises IntegrityError:
        """
        async with self.engine.begin() as conn:
            review_id = (
                await conn.execute(insert(ProductReview).values(new_review.model_dump()))
            ).inserted_primary_key[0]

        self.logger.debug(
            f"product_review_id={review_id}: added product_review {review_id} {new_review}",
            extra=extra_params(product_review=review_id)
        )

        return review_id

    @validate_call(validate_return=True)
    async def update_product_review(self, updated_review: ProductReviewSchema) -> None:
        await self.get_product_review(updated_review.id)
        async with self.engine.begin() as conn:
            await conn.execute(
                update(ProductReview).where(ProductReview.id == updated_review.id).values(updated_review.model_dump())
            )

        self.logger.debug(
            f"product_review_id={updated_review.id}: updated product_review {updated_review}",
            extra=extra_params(product_review=updated_review.id)
        )

    @validate_call(validate_return=True)
    async def delete_product_review(self, review_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(ProductReview).where(ProductReview.id == review_id))

        self.logger.debug(
            f"product_review_id={review_id}: deleted product_review {review_id}",
            extra=extra_params(product_review=review_id)
        )
