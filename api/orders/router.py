from database.models.order_model import OrderSchema, OrderWithoutId, OrderNotFound
from loader import db_engine, logger
from fastapi import HTTPException, APIRouter
from pydantic import ValidationError
from datetime import datetime
import random
import string

PATH = "/api/orders"
router = APIRouter(
    prefix=PATH,
    tags=["orders"],
    responses={404: {"description": "Order not found"}},
)

db = db_engine.get_order_dao()


@router.get("/generate_order_id")
async def generate_order_id_api() -> str:
    date = datetime.now().strftime("%d%m%y")
    random_string = ''.join(random.sample(string.digits + string.ascii_letters, 5))
    order_id = date + random_string
    try:
        await db.get_order(order_id)
    except OrderNotFound:
        return random_string
    logger.info("generated order_id already exist, regenerating...")
    await generate_order_id_api()


@router.get("/get_all_orders/{token}")
async def get_all_orders_api(token: str) -> list[OrderSchema]:
    token = token.replace('_', ':', 1)
    try:
        orders = await db.get_all_orders(token)
    except ValidationError as ex:
        logger.warning("validation error", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Incorrect input data.\n{str(ex)}")
    except Exception:
        logger.error("Error while execute get_all_orders db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return orders


@router.get("/get_order/{token}/{order_id}")
async def get_order_api(token: str, order_id: str) -> OrderSchema:
    try:
        order = await db.get_order(order_id)
    except OrderNotFound:
        raise HTTPException(status_code=404, detail="Product not found.")
    except ValidationError as ex:
        raise HTTPException(status_code=400, detail=f"Incorrect input data.\n{str(ex)}")
    except Exception:
        logger.error("Error while execute get_order db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return order


@router.post("/add_order")
async def add_order_api(new_order: OrderWithoutId) -> OrderSchema:
    try:
        new_order.ordered_at = new_order.ordered_at.replace(tzinfo=None)
        order = await db.add_order(new_order)
    except ValidationError as ex:
        logger.warning("incorrect data in request", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Incorrect input data.\n{str(ex)}")
    except Exception:
        logger.error("Error while execute add_order db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return order


@router.post("/update_order")
async def update_order_api(updated_order: OrderWithoutId) -> str:
    try:
        order = await db.update_order(updated_order)
    except OrderNotFound:
        raise HTTPException(status_code=404, detail="Product not found.")
    except ValidationError as ex:
        raise HTTPException(status_code=400, detail="Incorrect input data.\n{str(ex)}")
    except Exception:
        logger.error("Error while execute add_order db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return "updated"


@router.delete("/delete_order/{token}/{order_id}")
async def delete_order_api(token: str, order_id: str) -> str:
    try:
        await db.delete_order(order_id)
    except OrderNotFound:
        raise HTTPException(status_code=404, detail="Product not found.")
    except ValidationError:
        raise HTTPException(status_code=400, detail="Incorrect input data.")
    except Exception:
        logger.error("Error while execute add_order db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return "deleted"
