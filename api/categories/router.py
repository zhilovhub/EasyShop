from database.models.category_model import CategorySchema, CategoryDao, CategorySchemaWithoutId
from database.models.product_model import ProductSchema, ProductNotFound, ProductWithoutId, ProductDao
from loader import db_engine
from fastapi import HTTPException, APIRouter, File, UploadFile, Header
from typing import Annotated
from pydantic import BaseModel
from products.router import check_admin_authorization

from logs.config import api_logger, extra_params

PATH = "/api/categories"
router = APIRouter(
    prefix=PATH,
    tags=["categories"],
    responses={404: {"description": "Category not found"}},
)
product_db: ProductDao = db_engine.get_product_db()
category_db: CategoryDao = db_engine.get_category_dao()


@router.get("/get_all_categories/{bot_id}")
async def get_all_categories_api(bot_id: int) -> list[CategorySchema]:
    try:
        categories = await category_db.get_all_categories(bot_id)
        api_logger.debug(
            f"bot_id={bot_id}: has {len(categories)} categories: {categories}",
            extra=extra_params(bot_id=bot_id)
        )
    except Exception:
        api_logger.error(
            "Error while execute get_all_categories db_method",
            extra=extra_params(bot_id=bot_id)
        )
        raise HTTPException(status_code=500, detail="Internal error.")
    return categories


@router.post("/add_category")
async def add_category_api(new_category: CategorySchemaWithoutId, authorization_hash: str = Header()) -> int:
    await check_admin_authorization(new_category.bot_id, authorization_hash)
    try:
        cat_id = await category_db.add_category(new_category)
        api_logger.debug(
            f"bot_id={new_category.bot_id}: added cat_id={cat_id}, category {new_category}",
            extra=extra_params(bot_id=new_category.bot_id, category_id=cat_id)
        )
    except Exception:
        api_logger.error(
            "Error while execute add_category db_method",
            extra=extra_params(bot_id=new_category.bot_id)
        )
        raise HTTPException(status_code=500, detail="Internal error.")
    return cat_id


@router.post("/edit_category")
async def edit_category_api(category: CategorySchema, authorization_hash: str = Header()) -> bool:
    await check_admin_authorization(category.bot_id, authorization_hash)
    try:
        await category_db.update_category(category)
        api_logger.debug(
            f"bot_id={category.bot_id}: updated category {category}",
            extra=extra_params(bot_id=category.bot_id, category_id=category.id)
        )
    except Exception:
        api_logger.error(
            "Error while execute update_category db_method",
            extra=extra_params(bot_id=category.bot_id, category_id=category.id)
        )
        raise HTTPException(status_code=500, detail="Internal error.")
    return True
