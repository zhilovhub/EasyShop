from database.models.models import Database
from database.models.product_model import ProductSchema, ProductNotFound

from logs.config import logger, extra_params


async def get_product_by_id(product_id: int) -> ProductSchema | None:
    try:
        product = await Database().get_product(product_id=product_id)
        return product
    except ProductNotFound:
        logger.debug(
            f"product_id={product_id}: not found",
            extra=extra_params(product_id=product_id)
        )
        return None
