from pydantic import BaseModel, ConfigDict, Field, validate_call
from sqlalchemy import Column, BigInteger, String, select, ForeignKey, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.bot_model import Bot
from database.models.dao import Dao


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

    bot_id = Field(frozen=True)
    name: str


class CategorySchema(CategorySchemaWithoutId):
    id: int = Field(frozen=True)


class CategoryDao(Dao):
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

        self.logger.info(f"get_all_categories method with bot_id: {bot_id} success")
        return res

    @validate_call(validate_return=True)
    async def get_category(self, category_id: int) -> CategorySchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Category).where(Category.id == category_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()

        self.logger.info(f"get_category method with category_id: {category_id} success")
        return res

    @validate_call
    async def add_category(self, new_category: CategorySchemaWithoutId) -> None:
        if type(new_category) != CategorySchemaWithoutId:
            raise InvalidParameterFormat("category_schema must be type of CategorySchemaWithoutId")

        async with self.engine.begin() as conn:
            all_categories = await self.get_all_categories(new_category.bot_id)
            if new_category.name in list(map(lambda x: x.name, all_categories)):
                raise SameCategoryNameAlreadyExists(
                    f"category name {new_category.name} already exists in bot_id = {new_category.bot_id}"
                )
            await conn.execute(insert(Category).values(new_category.model_dump()))

        self.logger.info(f"successfully add new_category {new_category} to db")

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
        self.logger.info(f"successfully update category with id {updated_category.id} at db")

    @validate_call
    async def delete_category(self, category_id: int):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Category).where(Category.id == category_id))
        self.logger.info(f"deleted category with id {category_id}")
