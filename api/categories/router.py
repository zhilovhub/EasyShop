from database.models.category_model import CategorySchema, CategoryDao, CategorySchemaWithoutId
from database.models.product_model import ProductSchema, ProductNotFound, ProductWithoutId, ProductDao
from loader import db_engine, logger
from fastapi import HTTPException, APIRouter, File, UploadFile
from typing import Annotated
from pydantic import BaseModel


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
    except Exception:
        logger.error("Error while execute get_all_categories db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return categories


@router.post("/add_category")
async def add_category_api(new_category: CategorySchemaWithoutId) -> int:
    try:
        cat_id = await category_db.add_category(new_category)
    except Exception:
        logger.error("Error while execute add_category db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return cat_id


@router.post("/edit_category")
async def edit_category_api(category: CategorySchema) -> bool:
    try:
        await category_db.update_category(category)
    except Exception:
        logger.error("Error while execute update_category db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return True
