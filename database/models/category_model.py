from pydantic import BaseModel, ConfigDict, Field, validate_call

from sqlalchemy import Column, BigInteger, String, select, ForeignKey, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat

from database.models import Base
from database.models.dao import Dao
from database.models.bot_model import Bot

from logs.config import extra_params


class SameCategoryNameAlreadyExists(Exception):
    """Raised when trying to add category with name already exists in bot"""
    pass


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
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Category).where(Category.bot_id == bot_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for category in raw_res:
            res.append(CategorySchema.model_validate(category))

        self.logger.debug(
            f"bot_id={bot_id}: has {len(res)} categories",
            extra=extra_params(bot_id=bot_id)
        )

        return res

    @validate_call
    async def get_category(self, category_id: int) -> CategorySchema | None:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Category).where(Category.id == category_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()

        if res is not None:
            self.logger.debug(
                f"category_id={category_id}: category {category_id} is found",
                extra=extra_params(category_id=category_id)
            )

        return res

    @validate_call
    async def add_category(self, new_category: CategorySchemaWithoutId) -> int:
        if type(new_category) != CategorySchemaWithoutId:
            raise InvalidParameterFormat("category_schema must be type of CategorySchemaWithoutId")

        async with self.engine.begin() as conn:
            all_categories = await self.get_all_categories(new_category.bot_id)
            if new_category.name in list(map(lambda x: x.name, all_categories)):
                raise SameCategoryNameAlreadyExists(
                    f"category name {new_category.name} already exists in bot_id = {new_category.bot_id}"
                )
            cat_id = (await conn.execute(insert(Category).values(new_category.model_dump()))).inserted_primary_key[0]

        self.logger.debug(
            f"category_id={cat_id}: category {cat_id} is added to database",
            extra=extra_params(bot_id=new_category.bot_id, category_id=cat_id)
        )

        return cat_id

    @validate_call
    async def update_category(self, updated_category: CategorySchema) -> None:
        await self.get_category(updated_category.id)
        async with self.engine.begin() as conn:
            all_categories = await self.get_all_categories(updated_category.bot_id)
            if updated_category.name in list(map(lambda x: x.name, all_categories)):
                raise SameCategoryNameAlreadyExists(
                    f"category name {updated_category.name} already exists in bot_id = {updated_category.bot_id}"
                )
            await conn.execute(
                update(Category).where(Category.id == updated_category.id).values(updated_category.model_dump())
            )

        self.logger.debug(
            f"category_id={updated_category.id}: category {updated_category.id} is updated",
            extra=extra_params(bot_id=updated_category.bot_id, category_id=updated_category.id)
        )

    @validate_call
    async def delete_category(self, category_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Category).where(Category.id == category_id))

        self.logger.debug(
            f"category_id={category_id}: category {category_id} is deleted",
            extra=extra_params(category_id=category_id)
        )
