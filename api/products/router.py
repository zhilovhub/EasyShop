from database.models.product_model import ProductSchema, ProductNotFound
from loader import db_engine, logger
from fastapi import HTTPException, APIRouter


PATH = "/api/products"
router = APIRouter(
    prefix=PATH,
    tags=["products"],
    responses={404: {"description": "Product not found"}},
)
db = db_engine.get_product_db()


@router.get("/get_all_products/{bot_id}")
async def get_all_products_api(bot_id: int) -> list[ProductSchema]:
    try:
        products = await db.get_all_products(bot_id)
    except Exception:
        logger.error("Error while execute get_all_products db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return products


@router.get("/get_product/{bot_id}/{product_id}")
async def get_product_api(bot_id: int, product_id: int) -> ProductSchema:
    try:
        product = await db.get_product(product_id)
    except ProductNotFound:
        raise HTTPException(status_code=404, detail="Product not found.")
    except Exception:
        logger.error("Error while execute get_product db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return product

