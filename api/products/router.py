import random
import string

from fastapi import APIRouter, UploadFile, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from api.utils import (check_admin_authorization, SearchWordMustNotBeEmptyError, HTTPProductNotFoundError,
                       HTTPInternalError, HTTPBadRequestError, HTTPConflictError, RESPONSES_DICT,
                       HTTPCustomBotIsOfflineError, HTTPBotNotFoundError)
from common_utils.env_config import FILES_PATH

from database.models.bot_model import BotNotFoundError
from database.config import product_db, category_db, bot_db
from database.models.product_model import (
    ProductSchema,
    ProductNotFoundError,
    ProductWithoutId,
    ProductFilter,
    ProductFilterWithoutBot,
    FilterNotFoundError,
    PRODUCT_FILTERS)

from logs.config import api_logger, extra_params

PATH = "/api/products"
router = APIRouter(
    prefix=PATH,
    tags=["products"],
    responses=RESPONSES_DICT,
)


class GetProductsRequest(BaseModel):
    """Filter Parameters for get_all_products request"""

    bot_id: int = Field(frozen=True)
    price_min: int = 0
    price_max: int = 2147483647
    search_word: str | None = None
    filters: list[ProductFilterWithoutBot] | None


def _remove_empty_variants(product: ProductWithoutId | ProductSchema) -> ProductWithoutId | ProductSchema:
    """
    Removes empty variants from extra options of product

    :return: product with extra_options without None or '' variants
    """
    options = product.extra_options
    formatted_options = []
    if options:
        for option in options:
            option.variants = list(filter(lambda x: x, option.variants))
            if option.variants_prices:
                option.variants_prices = list(filter(lambda x: x, option.variants_prices))
            formatted_options.append(option)
        product.extra_options = formatted_options
    return product


@router.get("/get_filters/")
async def get_filters_api():
    api_logger.debug(
        f"/get_filters/ has returned {PRODUCT_FILTERS}"
    )

    return PRODUCT_FILTERS


@router.post("/get_all_products/")
async def get_all_products_api(payload: GetProductsRequest = Depends(
        GetProductsRequest)) -> list[ProductSchema]:
    """
    :raises HTTPBadRequestError:
    :raises HTTPBotNotFoundError:
    :raises HTTPCustomBotIsOfflineError:
    :raises SearchWordMustNotBeEmptyError:
    :raises HTTPInternalError:
    """
    try:
        bot = await bot_db.get_bot(payload.bot_id)
    except BotNotFoundError:
        raise HTTPBotNotFoundError(bot_id=payload.bot_id)

    if bot.status != "online":
        raise HTTPCustomBotIsOfflineError(bot_id=bot.bot_id)

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
                        raise SearchWordMustNotBeEmptyError
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
    except FilterNotFoundError as ex:
        api_logger.error(
            f"bot_id={payload.bot_id}: {ex.message}",
            extra=extra_params(bot_id=payload.bot_id)
        )
        raise HTTPBadRequestError(detail_message=ex.message)
    except SearchWordMustNotBeEmptyError:
        api_logger.error(
            f"bot_id={payload.bot_id}: SearchWordMustNotBeEmpty with {payload}",
            extra=extra_params(bot_id=payload.bot_id)
        )
        raise HTTPBadRequestError(detail_message="'search' filter is provided, search_word must not be empty")
    except Exception as e:
        api_logger.error(
            f"bot_id={payload.bot_id}: Error while execute get_all_products db_method",
            extra=extra_params(bot_id=payload.bot_id),
            exc_info=e
        )
        raise HTTPInternalError

    api_logger.info(
        f"bot_id={payload.bot_id}: has {len(products)} products -> {products}",
        extra=extra_params(bot_id=payload.bot_id)
    )

    return products


@router.get("/get_product/{bot_id}/{product_id}")
async def get_product_api(bot_id: int, product_id: int) -> ProductSchema:
    """
    :raises HTTPInternalError:
    :raises HTTPProductNotFoundError:
    """
    try:
        product = await product_db.get_product(product_id)

    except ProductNotFoundError as e:
        api_logger.error(
            f"bot_id={bot_id}: product_id={product_id} is not found in database",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        raise HTTPProductNotFoundError(product_id=product_id, bot_id=bot_id)

    except Exception as e:
        api_logger.error(
            f"bot_id={bot_id}: Error while execute get_product db_method with product_id={product_id}",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        raise HTTPInternalError

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
    """
    :raises HTTPException:
    :raises HTTPConflictError:
    :raises HTTPInternalError:
    """
    await check_admin_authorization(new_product.bot_id, authorization_data)
    try:
        new_product = _remove_empty_variants(new_product)
        product_id = await product_db.add_product(new_product)

    except IntegrityError as ex:
        api_logger.error(
            f"bot_id={new_product.bot_id}: "
            f"IntegrityError while execute add_product db_method with product={new_product}",
            extra=extra_params(bot_id=new_product.bot_id),
            exc_info=ex
        )
        raise HTTPConflictError(detail_message="Conflict while adding product (Item already exists)", ex_msg=ex.detail)

    except Exception as e:
        api_logger.error(
            f"bot_id={new_product.bot_id}: Error while execute add_product db_method with product={new_product}",
            extra=extra_params(bot_id=new_product.bot_id),
            exc_info=e
        )
        raise HTTPInternalError

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
    """
    Updates product.picture in database and saves photo on directory

    :raises HTTPException:
    :raises HTTPProductNotFoundError:
    """

    await check_admin_authorization(bot_id, authorization_data)

    try:
        product = await product_db.get_product(product_id)
        product.picture = []

        for file in files:
            random_string = ''.join(
                random.sample(
                    string.digits +
                    string.ascii_letters,
                    15))
            photo_path = f"{bot_id}_{random_string}.{file.filename.split('.')[-1]}"

            api_logger.debug(
                f"bot_id={bot_id}: downloading new file in directory {photo_path} for product_id={product_id}",
                extra=extra_params(bot_id=bot_id, product_id=product_id)
            )

            with open(FILES_PATH + photo_path, "wb") as photo:
                photo.write(await file.read())

            product.picture.append(photo_path)
        await product_db.update_product(product)

    except ProductNotFoundError as e:
        api_logger.error(
            f"bot_id={bot_id}: product_id={product_id} is not found in database",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        raise HTTPProductNotFoundError(product_id=product_id, bot_id=bot_id)
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
    """
    :raises HTTPException:
    :raises HTTPInternalError:
    """

    await check_admin_authorization(product.bot_id, authorization_data)
    try:
        product = _remove_empty_variants(product)
        await product_db.update_product(product, exclude_pictures=True)
    except Exception as e:
        api_logger.error(
            f"bot_id={product.bot_id}: Error while execute update_product db_method with product={product}",
            extra=extra_params(bot_id=product.bot_id, product_id=product.id),
            exc_info=e
        )
        raise HTTPInternalError

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
    """
    :raises HTTPException:
    :raises ProductNotFoundError:
    :raises HTTPInternalError:
    """

    await check_admin_authorization(bot_id, authorization_data)

    try:
        await product_db.delete_product(product_id)
    except ProductNotFoundError as e:
        api_logger.error(
            f"bot_id={bot_id}: product_id={product_id} is not found in database",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        raise HTTPProductNotFoundError(product_id=product_id, bot_id=bot_id)
    except Exception as e:
        api_logger.error(
            f"bot_id={bot_id}: Error while execute delete_product db_method with product_id={product_id}",
            extra=extra_params(bot_id=bot_id, product_id=product_id),
            exc_info=e
        )
        raise HTTPInternalError

    api_logger.debug(
        f"bot_id={bot_id}: product_id={product_id} is delete from database",
        extra=extra_params(bot_id=bot_id, product_id=product_id)
    )

    return "product deleted"
