from fastapi import APIRouter, Header

from database.config import category_db
from database.models.category_model import CategorySchema, CategorySchemaWithoutId, CategoryNameAlreadyExistsError

from api.utils import check_admin_authorization, RESPONSES_DICT, HTTPInternalError, HTTPConflictError

from logs.config import api_logger, extra_params

PATH = "/categories"
router = APIRouter(
    prefix=PATH,
    tags=["categories"],
    responses=RESPONSES_DICT,
)


@router.get("/get_all_categories/{bot_id}")
async def get_all_categories_api(bot_id: int) -> list[CategorySchema]:
    """
    :raises HTTPInternalError:
    """
    try:
        categories = await category_db.get_all_categories(bot_id)
        api_logger.debug(
            f"bot_id={bot_id}: has {len(categories)} categories: {categories}", extra=extra_params(bot_id=bot_id)
        )
    except Exception as e:
        api_logger.error(
            "Error while execute get_all_categories db_method", extra=extra_params(bot_id=bot_id), exc_info=e
        )
        raise HTTPInternalError
    return categories


@router.post("/add_category")
async def add_category_api(new_category: CategorySchemaWithoutId, authorization_data: str = Header()) -> int:
    """
    :raises HTTPInternalError:
    :raises HTTPConflictError:
    :raises HTTPException:
    """
    await check_admin_authorization(new_category.bot_id, authorization_data)
    try:
        cat_id = await category_db.add_category(new_category)
        api_logger.debug(
            f"bot_id={new_category.bot_id}: added cat_id={cat_id}, category {new_category}",
            extra=extra_params(bot_id=new_category.bot_id, category_id=cat_id),
        )
    except CategoryNameAlreadyExistsError:
        raise HTTPConflictError(
            detail_message="Conflict while adding category (category with provided name already exists).",
            category_name=new_category.name,
        )
    except Exception as e:
        api_logger.error(
            "Error while execute add_category db_method", extra=extra_params(bot_id=new_category.bot_id), exc_info=e
        )
        raise HTTPInternalError
    return cat_id


@router.post("/edit_category")
async def edit_category_api(category: CategorySchema, authorization_data: str = Header()) -> bool:
    """
    :raises HTTPInternalError:
    :raises HTTPException:
    """
    await check_admin_authorization(category.bot_id, authorization_data)
    try:
        await category_db.update_category(category)
        api_logger.debug(
            f"bot_id={category.bot_id}: updated category {category}",
            extra=extra_params(bot_id=category.bot_id, category_id=category.id),
        )
    # TODO uncomment after pull request with db method updating
    # except CategoryNotFound:
    #     raise HTTPCategoryNotFound(bot_id=category.bot_id, category_id=category.id)
    except Exception as e:
        api_logger.error(
            "Error while execute update_category db_method",
            extra=extra_params(bot_id=category.bot_id, category_id=category.id),
            exc_info=e,
        )
        raise HTTPInternalError
    return True
