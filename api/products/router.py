import random
import string
from typing import Annotated

from fastapi import HTTPException, APIRouter, File, UploadFile, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from api.utils import check_admin_authorization
from api.loader import db_engine, PROJECT_ROOT

from database.models.product_model import (
    ProductSchema,
    ProductNotFound,
    ProductWithoutId,
    ProductDao,
    ProductFilter,
    ProductFilterWithoutBot,
    FilterNotFound,
    PRODUCT_FILTERS)
from database.models.category_model import CategoryDao

from logs.config import api_logger, extra_params

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
    api_logger.debug(
        f"/get_filters/ has returned {PRODUCT_FILTERS}"
    )

    return PRODUCT_FILTERS


@router.post("/get_all_products/")
async def get_all_products_api(payload: GetProductsRequest = Depends(
        GetProductsRequest)) -> list[ProductSchema]:
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
                    filters.append(
                        ProductFilter(
                            bot_id=payload.bot_id,
                            filter_name=product_filter.filter_name,
                            is_category_filter=product_filter.is_category_filter,
                            reverse_order=product_filter.reverse_order,
                            category_id=cat_id,
                            search_word=None))
                elif product_filter.filter_name == "search":
                    if payload.search_word is None:
                        raise SearchWordMustNotBeEmpty
                    filters.append(
                        ProductFilter(
                            bot_id=payload.bot_id,
                            filter_name=product_filter.filter_name,
                            is_category_filter=product_filter.is_category_filter,
                            reverse_order=product_filter.reverse_order,
                            category_id=None,
                            search_word=payload.search_word))
                else:
                    filters.append(
                        ProductFilter(
                            bot_id=payload.bot_id,
                            filter_name=product_filter.filter_name,
                            is_category_filter=product_filter.is_category_filter,
                            reverse_order=product_filter.reverse_order,
                            category_id=None,
                            search_word=None))
            products = await product_db.get_all_products(payload.bot_id,
                                                         price_min=payload.price_min,
                                                         price_max=payload.price_max,
                                                         filters=filters)
    except FilterNotFound as ex:
        api_logger.error(
            f"bot_id={payload.bot_id}: {ex.message}",
            extra=extra_params(bot_id=payload.bot_id)
        )
        raise HTTPException(status_code=400, detail=ex.message)
    except SearchWordMustNotBeEmpty:
        api_logger.error(
            f"bot_id={payload.bot_id}: SearchWordMustNotBeEmpty with {payload}",
            extra=extra_params(bot_id=payload.bot_id)
        )
        raise HTTPException(
            status_code=400,
            detail="'search' filter is provided, search_word must not be empty")
    # except CategoryFilterNotFound as ex:
    #     raise HTTPException(status_code=400, detail=ex.message)
    except Exception as e:
        api_logger.error(
            f"bot_id={payload.bot_id}: Error while execute get_all_products db_method",
            extra=extra_params(bot_id=payload.bot_id),
            exc_info=e
        )
        raise HTTPException(status_code=500, detail="Internal error.")

    api_logger.info(
        f"bot_id={payload.bot_id}: has {len(products)} products -> {products}",
        extra=extra_params(bot_id=payload.bot_id)
    )

    return products


@router.get("/get_product/{bot_id}/{product_id}")
async def get_product_api(bot_id: int, product_id: int) -> ProductSchema:
    try:
        product = await product_db.get_product(product_id)

    except ProductNotFound as e:
        api_logger.error(
            f"bot_id={bot_id}: product_id={product_id} is not found in database",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        raise HTTPException(status_code=404, detail="Product not found.")

    except Exception as e:
        api_logger.error(
            f"bot_id={bot_id}: Error while execute get_product db_method with product_id={product_id}",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        raise HTTPException(status_code=500, detail="Internal error.")

    api_logger.debug(
        f"bot_id={bot_id}: product_id={product_id} is found database -> {product}",
        extra=extra_params(bot_id=bot_id, product_id=product_id)
    )

    return product


@router.post("/add_product")
async def add_product_api(
        new_product: ProductWithoutId,
        authorization_data: str = Header(),
) -> int:
    await check_admin_authorization(new_product.bot_id, authorization_data)
    try:
        product_id = await product_db.add_product(new_product)

    except IntegrityError as ex:
        api_logger.error(
            f"bot_id={new_product.bot_id}: "
            f"IntegrityError while execute add_product db_method with product={new_product}",
            extra=extra_params(bot_id=new_product.bot_id),
            exc_info=ex
        )
        raise HTTPException(status_code=409, detail=str(ex))

    except Exception as e:
        api_logger.error(
            f"bot_id={new_product.bot_id}: Error while execute add_product db_method with product={new_product}",
            extra=extra_params(bot_id=new_product.bot_id),
            exc_info=e
        )
        raise HTTPException(status_code=500, detail="Internal error.")

    api_logger.debug(
        f"bot_id={new_product.bot_id}: product_id={product_id} has been added to database -> {new_product}",
        extra=extra_params(bot_id=new_product.bot_id, product_id=product_id)
    )

    return product_id


@router.post("/add_product_photo")
async def create_file(bot_id: int,
                      product_id: int,
                      files: list[UploadFile],
                      authorization_data: str = Header()):
    await check_admin_authorization(bot_id, authorization_data)

    try:
        product = await product_db.get_product(product_id)
        for file in files:
            random_string = ''.join(
                random.sample(
                    string.digits +
                    string.ascii_letters,
                    15))
            files_path = f"{PROJECT_ROOT}Files/"
            photo_path = f"{bot_id}_{random_string}.{file.filename.split('.')[-1]}"

            api_logger.debug(
                f"bot_id={bot_id}: downloading new file in directory {photo_path} for product_id={product_id}",
                extra=extra_params(bot_id=bot_id, product_id=product_id)
            )

            with open(files_path + photo_path, "wb") as photo:
                photo.write(await file.read())

            if not product.picture:
                product.picture = []
            product.picture.append(photo_path)
        await product_db.update_product(product)

    except ProductNotFound as e:
        api_logger.error(
            f"bot_id={bot_id}: product_id={product_id} is not found in database",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        return HTTPException(status_code=404,
                             detail="Product with provided id not found")
    except BaseException as e:
        api_logger.error(
            f"bot_id={bot_id}: Error while adding photos to product_id={product_id}",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        raise

    api_logger.debug(
        f"bot_id={bot_id}: {len(files)} photos added to product_id={product_id}",
        extra=extra_params(bot_id=bot_id, product_id=product_id)
    )

    return f"{len(files)} photo added to product"


@router.post("/edit_product")
async def edit_product_api(
        product: ProductSchema,
        authorization_data: str = Header()) -> bool:
    await check_admin_authorization(product.bot_id, authorization_data)

    try:
        await product_db.update_product(product)
    except Exception as e:
        api_logger.error(
            f"bot_id={product.bot_id}: Error while execute update_product db_method with product={product}",
            extra=extra_params(bot_id=product.bot_id, product_id=product.id),
            exc_info=e
        )
        raise HTTPException(status_code=500, detail="Internal error.")

    api_logger.debug(
        f"bot_id={product.bot_id}: updated product={product}",
        extra=extra_params(bot_id=product.bot_id, product_id=product.id)
    )

    return True


@router.delete("/del_product/{bot_id}/{product_id}")
async def delete_product_api(
        bot_id: int,
        product_id: int,
        authorization_data: str = Header()) -> str:
    await check_admin_authorization(bot_id, authorization_data)

    try:
        await product_db.delete_product(product_id)
    except ProductNotFound as e:
        api_logger.error(
            f"bot_id={bot_id}: product_id={product_id} is not found in database",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        raise HTTPException(status_code=404, detail="Product not found.")
    except Exception as e:
        api_logger.error(
            f"bot_id={bot_id}: Error while execute delete_product db_method with product_id={product_id}",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        raise HTTPException(status_code=500, detail="Internal error.")

    api_logger.debug(
        f"bot_id={bot_id}: product_id={product_id} is delete from database",
        extra=extra_params(bot_id=bot_id, product_id=product_id)
    )

    return "product deleted"


class CSVFileInputModel(BaseModel):
    """Models updatable field of a profile instance"""
    bot_id: int
    file: bytes


@router.post("/send_product_csv_file")
async def send_product_csv_api(
        payload: CSVFileInputModel,
        authorization_data: str = Header()) -> bool:
    await check_admin_authorization(payload.bot_id, authorization_data)
    try:
        api_logger.info(f"get new csv file from api method bytes: {payload.file}")
    except Exception as e:
        api_logger.error("Error while execute send_product_csv api method", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal error.")
    return True


@router.get("/get_products_csv_file/{bot_id}")
async def get_product_csv_api(
        bot_id: int, authorization_data: str = Header()) -> Annotated[bytes, File()]:
    await check_admin_authorization(bot_id, authorization_data)
    try:
        # get csv logic
        pass
    except Exception as e:
        api_logger.error("Error while execute get_product_csv api method", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal error.")
    return bytes(200)
