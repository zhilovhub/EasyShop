from database.models.category_model import CategorySchema, CategoryDao
from database.models.product_model import (ProductSchema, ProductNotFound, ProductWithoutId, ProductDao,
                                           ProductFilter, ProductFilterWithoutBot, FilterNotFound, PRODUCT_FILTERS)
from loader import db_engine, logger
from fastapi import HTTPException, APIRouter, File, UploadFile, Body, Depends
from typing import Annotated, List
from pydantic import BaseModel, Field, field_validator, InstanceOf, model_validator


PATH = "/api/products"
router = APIRouter(
    prefix=PATH,
    tags=["products"],
    responses={404: {"description": "Product not found"}},
)
product_db: ProductDao = db_engine.get_product_db()
category_db: CategoryDao = db_engine.get_category_dao()


class GetProductsRequest(BaseModel):
    bot_id: int = Field(frozen=True)
    price_min: int = 0
    price_max: int = 2147483647
    filters: list[ProductFilterWithoutBot] | None


@router.get("/get_filters/")
async def get_filters_api():
    return PRODUCT_FILTERS


@router.post("/get_all_products/")
async def get_all_products_api(payload: GetProductsRequest = Depends(GetProductsRequest)) -> list[ProductSchema]:
    try:
        if not payload.filters:
            products = await product_db.get_all_products(payload.bot_id,
                                                         price_min=payload.price_min,
                                                         price_max=payload.price_max)
        else:
            filters: list[ProductFilter] = []
            for product_filter in payload.filters:
                if product_filter.is_category_filter:
                    cats = await category_db.get_all_categories(payload.bot_id)
                    cat_id = None
                    for cat in cats:
                        if cat.name.lower() == product_filter.filter_name.lower():
                            cat_id = cat.id
                            break
                    filters.append(ProductFilter(bot_id=payload.bot_id, filter_name=product_filter.filter_name,
                                                 is_category_filter=product_filter.is_category_filter,
                                                 reverse_order=product_filter.reverse_order,
                                                 category_id=cat_id))
                else:
                    filters.append(ProductFilter(bot_id=payload.bot_id, filter_name=product_filter.filter_name,
                                                 is_category_filter=product_filter.is_category_filter,
                                                 reverse_order=product_filter.reverse_order,
                                                 category_id=None))
            products = await product_db.get_all_products(payload.bot_id,
                                                         price_min=payload.price_min,
                                                         price_max=payload.price_max,
                                                         filters=filters)
    except FilterNotFound as ex:
        raise HTTPException(status_code=400, detail=ex.message)
    # except CategoryFilterNotFound as ex:
    #     raise HTTPException(status_code=400, detail=ex.message)
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


@router.post("/edit_product")
async def edit_product_api(product: ProductSchema) -> bool:
    try:
        await product_db.update_product(product)
    except Exception:
        logger.error("Error while execute update_product db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return True


class CSVFileInputModel(BaseModel):
    """Models updatable field of a profile instance"""
    bot_id: int
    file: bytes


@router.post("/send_product_csv_file")
async def send_product_csv_api(payload: CSVFileInputModel) -> bool:
    try:
        logger.info(f"get new csv file from api method bytes: {payload.file}")
    except Exception:
        logger.error("Error while execute send_product_csv api method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return True


@router.get("/get_products_csv_file/{bot_id}")
async def get_product_csv_api(bot_id: int) -> Annotated[bytes, File()]:
    try:
        # get csv logic
        pass
    except Exception:
        logger.error("Error while execute get_product_csv api method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return bytes(200)
