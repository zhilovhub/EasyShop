from database.models.product_model import ProductSchema, ProductDao, ProductNotFound
from ..main import db_engine, app, logger
from fastapi import HTTPException


PATH = "/api/products"
db = db_engine.get_product_db()


@app.get(PATH + "/get_all_products/{token}", tags=['products'])
async def get_all_products_api(token: str):
    try:
        products = await db.get_all_products(token)
    except Exception:
        logger.error("Error while execute get_all_products db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return products


@app.get(PATH + "/get_product/{token}/{product_id}", tags=['products'])
async def get_product_api(token: str, product_id: int):
    try:
        product = await db.get_product(token, product_id)
    except ProductNotFound:
        raise HTTPException(status_code=404, detail="Product not found.")
    except Exception:
        logger.error("Error while execute get_all_products db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return product

