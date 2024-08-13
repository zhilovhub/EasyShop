from pydantic import BaseModel, ConfigDict, Field, validate_call

from sqlalchemy import Column, BigInteger, String, select, ForeignKey, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from database.exceptions.exceptions import KwargsException

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot

from logs.config import extra_params


class CategoryNotFoundError(KwargsException):
    """Raised when provided category not found in database"""


class CategoryNameAlreadyExistsError(KwargsException):
    """Raised when provided category name is already taken from bot"""


class Category(Base):
    __tablename__ = "categories"

    id = Column(BigInteger, primary_key=True)
    bot_id = Column(ForeignKey(Bot.bot_id, ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)


class CategorySchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bot_id: int = Field(frozen=True)
    name: str


class CategorySchema(CategorySchemaWithoutId):
    id: int = Field(frozen=True)


class CategoryDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_categories(self, bot_id: int) -> list[CategorySchema]:
        """

        :param bot_id: bot_id from search
        :return: list of CategorySchema
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Category).where(Category.bot_id == bot_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for category in raw_res:
            res.append(CategorySchema.model_validate(category))

        self.logger.debug(f"bot_id={bot_id}: has {len(res)} categories", extra=extra_params(bot_id=bot_id))

        return res

    @validate_call(validate_return=True)
    async def get_category(self, category_id: int) -> CategorySchema:
        """
        :param category_id: category_id
        :return: CategorySchema

        :raises CategoryNotFoundError: no category in db
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Category).where(Category.id == category_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise CategoryNotFoundError(category_id=category_id)

        res = CategorySchema.model_validate(res)
        self.logger.debug(
            f"category_id={category_id}: found category {res}", extra=extra_params(category_id=category_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_category(self, new_category: CategorySchemaWithoutId) -> int:
        """
        :raises CategoryNameAlreadyExistsError:
        """
        async with self.engine.begin() as conn:
            all_categories = await self.get_all_categories(new_category.bot_id)
            for cat in all_categories:
                if new_category.name == cat.name:
                    raise CategoryNameAlreadyExistsError(
                        category_name=new_category.name, bot_id=new_category.bot_id, category_id=cat.id
                    )
            cat_id = (await conn.execute(insert(Category).values(new_category.model_dump()))).inserted_primary_key[0]

        self.logger.debug(
            f"category_id={cat_id}: new added category {new_category}",
            extra=extra_params(bot_id=new_category.bot_id, category_id=cat_id),
        )

        return cat_id

    @validate_call(validate_return=True)
    async def update_category(self, updated_category: CategorySchema) -> None:
        """
        :raises CategoryNameAlreadyExistsError:
        """
        bot_id, category_id = updated_category.bot_id, updated_category.id
        await self.get_category(category_id)

        async with self.engine.begin() as conn:
            all_categories = await self.get_all_categories(bot_id)
            if updated_category.name in list(map(lambda x: x.name, all_categories)):
                raise CategoryNameAlreadyExistsError(
                    category_name=updated_category.name, bot_id=bot_id, category_id=category_id
                )
            await conn.execute(update(Category).where(Category.id == category_id).values(updated_category.model_dump()))

        self.logger.debug(
            f"category_id={category_id}: updated category {updated_category}",
            extra=extra_params(bot_id=bot_id, category_id=category_id),
        )

    @validate_call
    async def delete_category(self, category_id: int) -> None:
        """
        Deletes the category from database
        """
        async with self.engine.begin() as conn:
            await conn.execute(delete(Category).where(Category.id == category_id))

        self.logger.debug(
            f"category_id={category_id}: deleted category {category_id}", extra=extra_params(category_id=category_id)
        )
