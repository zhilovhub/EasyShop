from database.models.category_model import CategorySchema, CategoryDao
from database.models.product_model import (ProductSchema, ProductNotFound, ProductWithoutId, ProductDao,
                                           ProductFilter, ProductFilterWithoutBot, FilterNotFound, PRODUCT_FILTERS)
from loader import db_engine, logger, DEBUG
from fastapi import HTTPException, APIRouter, File, UploadFile, Body, Depends, Header
from typing import Annotated, List
from pydantic import BaseModel, Field, field_validator, InstanceOf, model_validator
from sqlalchemy.exc import IntegrityError


async def check_admin_authorization(bot_id: int, header) -> bool:
    if header:
        if DEBUG and header == "DEBUG":
            return True
        # process hash logic
    raise HTTPException(status_code=401, detail="Unauthorized for that API method")


PATH = "/api/products"
router = APIRouter(
    prefix=PATH,
    tags=["products"],
    responses={404: {"description": "Product not found"}},
)
product_db: ProductDao = db_engine.get_product_db()
category_db: CategoryDao = db_engine.get_category_dao()


class SearchWordMustNotBeEmpty(Exception):
    """Raised when 'search' filter is provided but search word is empty string"""
    pass


class GetProductsRequest(BaseModel):
    bot_id: int = Field(frozen=True)
    price_min: int = 0
    price_max: int = 2147483647
    search_word: str | None = None
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
                    cat_id = -1
                    for cat in cats:
                        if cat.name.lower() == product_filter.filter_name.lower():
                            cat_id = cat.id
                            break
                    filters.append(ProductFilter(bot_id=payload.bot_id, filter_name=product_filter.filter_name,
                                                 is_category_filter=product_filter.is_category_filter,
                                                 reverse_order=product_filter.reverse_order,
                                                 category_id=cat_id,
                                                 search_word=None))
                elif product_filter.filter_name == "search":
                    if payload.search_word is None:
                        raise SearchWordMustNotBeEmpty
                    filters.append(ProductFilter(bot_id=payload.bot_id, filter_name=product_filter.filter_name,
                                                 is_category_filter=product_filter.is_category_filter,
                                                 reverse_order=product_filter.reverse_order,
                                                 category_id=None,
                                                 search_word=payload.search_word))
                else:
                    filters.append(ProductFilter(bot_id=payload.bot_id, filter_name=product_filter.filter_name,
                                                 is_category_filter=product_filter.is_category_filter,
                                                 reverse_order=product_filter.reverse_order,
                                                 category_id=None,
                                                 search_word=None))
            products = await product_db.get_all_products(payload.bot_id,
                                                         price_min=payload.price_min,
                                                         price_max=payload.price_max,
                                                         filters=filters)
    except FilterNotFound as ex:
        raise HTTPException(status_code=400, detail=ex.message)
    except SearchWordMustNotBeEmpty:
        raise HTTPException(status_code=400, detail="'search' filter is provided, search_word must not be empty")
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
async def add_product_api(new_product: ProductWithoutId, authorization_hash: str = Header()) -> int:
    await check_admin_authorization(new_product.bot_id, authorization_hash)
    try:
        product_id = await product_db.add_product(new_product)
    except IntegrityError as ex:
        raise HTTPException(status_code=409, detail=str(ex))
    except Exception:
        logger.error("Error while execute add_product db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return product_id


@router.post("/edit_product")
async def edit_product_api(product: ProductSchema, authorization_hash: str = Header()) -> bool:
    await check_admin_authorization(product.bot_id, authorization_hash)
    try:
        await product_db.update_product(product)
    except Exception:
        logger.error("Error while execute update_product db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return True


@router.delete("/del_product/{bot_id}/{product_id}")
async def get_product_api(bot_id: int, product_id: int, authorization_hash: str = Header()) -> str:
    await check_admin_authorization(bot_id, authorization_hash)
    try:
        await product_db.delete_product(product_id)
    except ProductNotFound:
        raise HTTPException(status_code=404, detail="Product not found.")
    except Exception:
        logger.error("Error while execute delete_product db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return "product deleted"


class CSVFileInputModel(BaseModel):
    """Models updatable field of a profile instance"""
    bot_id: int
    file: bytes


@router.post("/send_product_csv_file")
async def send_product_csv_api(payload: CSVFileInputModel, authorization_hash: str = Header()) -> bool:
    await check_admin_authorization(payload.bot_id, authorization_hash)
    try:
        logger.info(f"get new csv file from api method bytes: {payload.file}")
    except Exception:
        logger.error("Error while execute send_product_csv api method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return True


@router.get("/get_products_csv_file/{bot_id}")
async def get_product_csv_api(bot_id: int, authorization_hash: str = Header()) -> Annotated[bytes, File()]:
    await check_admin_authorization(bot_id, authorization_hash)
    try:
        # get csv logic
        pass
    except Exception:
        logger.error("Error while execute get_product_csv api method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return bytes(200)
