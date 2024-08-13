from database.config import product_db
from database.models.product_model import ProductSchema, ProductNotFoundError

from logs.config import logger, extra_params


async def get_product_by_id(product_id: int) -> ProductSchema | None:
    try:
        product = await product_db.get_product(product_id=product_id)
        return product
    except ProductNotFoundError:
        logger.debug(f"product_id={product_id}: not found", extra=extra_params(product_id=product_id))
        return None
