from database.models.category_model import CategorySchema, CategoryDao
from database.models.product_model import ProductSchema, ProductNotFound, ProductWithoutId, ProductDao
from loader import db_engine, logger
from fastapi import HTTPException, APIRouter


PATH = "/api/products"
router = APIRouter(
    prefix=PATH,
    tags=["products"],
    responses={404: {"description": "Product not found"}},
)
product_db: ProductDao = db_engine.get_product_db()
category_db: CategoryDao = db_engine.get_category_dao()


@router.get("/get_all_products/{bot_id}")
async def get_all_products_api(bot_id: int) -> list[ProductSchema]:
    try:
        products = await product_db.get_all_products(bot_id)
    except Exception:
        logger.error("Error while execute get_all_products db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return products


@router.get("/get_product/{bot_id}/{product_id}")
async def get_product_api(bot_id: int, product_id: int) -> ProductSchema:
    try:
        product = await product_db.get_product(product_id)
    except ProductNotFound:
        raise HTTPException(status_code=404, detail="Product not found.")
    except Exception:
        logger.error("Error while execute get_product db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return product


@router.post("/add_product")
async def add_product_api(new_product: ProductWithoutId) -> int:
    try:
        product_id = await product_db.add_product(new_product)
    except Exception:
        logger.error("Error while execute add_product db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return product_id


@router.get("/get_all_categories/{bot_id}")
async def get_all_categories_api(bot_id: int) -> list[CategorySchema]:
    try:
        categories = await category_db.get_all_categories(bot_id)
    except Exception:
        logger.error("Error while execute get_all_categories db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return categories
