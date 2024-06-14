from database.models.order_model import OrderNotFound, OrderSchema
from pydantic import ValidationError
from loader import db_engine
from fastapi import APIRouter, HTTPException, Depends, Header
from datetime import datetime
import random
import string
from utils import check_admin_authorization

from logs.config import api_logger, extra_params

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
        api_logger.debug(
            f"order_id={random_string}: order_id has been generated",
            extra=extra_params(order_id=random_string)
        )
        return random_string

    api_logger.warning("generated order_id already exist, regenerating...")
    await generate_order_id_api()


@router.get("/get_all_orders/{bot_id}")
async def get_all_orders_api(bot_id: int, authorization_data: str = Header()) -> list[OrderSchema]:
    await check_admin_authorization(bot_id, authorization_data)
    try:
        orders = await db.get_all_orders(bot_id)
    except ValidationError as ex:
        api_logger.error(
            f"bot_id={bot_id}: validation error",
            extra=extra_params(bot_id=bot_id)
        )
        raise HTTPException(status_code=400, detail=f"Incorrect input data.\n{str(ex)}")
    except Exception:
        api_logger.error(
            f"bot_id={bot_id}: Error while execute get_all_orders db_method",
            extra=extra_params(bot_id=bot_id)
        )
        raise HTTPException(status_code=500, detail="Internal error.")

    api_logger.debug(
        f"bot_id={bot_id}: has {len(orders)} orders -> {orders}",
        extra=extra_params(bot_id=bot_id)
    )

    return orders

#
# @router.get("/get_order/{bot_id}/{order_id}")
# async def get_order_api(bot_id: int, order_id: str, authorization_hash: str = Header()) -> OrderSchema:
#     await check_admin_authorization(bot_id, authorization_hash)
#     try:
#         order = await db.get_order(order_id)
#     except OrderNotFound:
#         raise HTTPException(status_code=404, detail="Product not found.")
#     except ValidationError as ex:
#         raise HTTPException(status_code=400, detail=f"Incorrect input data.\n{str(ex)}")
#     except Exception:
#         logger.error("Error while execute get_order db_method", exc_info=True)
#         raise HTTPException(status_code=500, detail="Internal error.")
#     return order


@router.post("/add_order")
async def add_order_api(new_order: OrderSchema = Depends(), authorization_data: str = Header()) -> str:
    await check_admin_authorization(new_order.bot_id, authorization_data)
    try:
        new_order.ordered_at = new_order.ordered_at.replace(tzinfo=None)
        await db.add_order(new_order)

        api_logger.debug(
            f"bot_id={new_order.bot_id}: order {new_order} has been added",
            extra=extra_params(bot_id=new_order.bot_id, order_id=new_order.id)
        )
    # except ValidationError as ex:
    #     logger.warning("incorrect data in request", exc_info=True)
    #     raise HTTPException(status_code=400, detail=f"Incorrect input data.\n{str(ex)}")
    except Exception:
        api_logger.error(
            f"Error while execute add_order db_method with {new_order}",
            extra=extra_params(bot_id=new_order.bot_id, order_id=new_order.id)
        )
        raise HTTPException(status_code=500, detail="Internal error.")

    return "success"
#
#
# @router.post("/update_order")
# async def update_order_api(updated_order: OrderWithoutId) -> str:
#     try:
#         order = await db.update_order(updated_order)
#     except OrderNotFound:
#         raise HTTPException(status_code=404, detail="Product not found.")
#     except ValidationError as ex:
#         raise HTTPException(status_code=400, detail="Incorrect input data.\n{str(ex)}")
#     except Exception:
#         logger.error("Error while execute add_order db_method", exc_info=True)
#         raise HTTPException(status_code=500, detail="Internal error.")
#     return "updated"
#
#
# @router.delete("/delete_order/{token}/{order_id}")
# async def delete_order_api(token: str, order_id: str) -> str:
#     try:
#         await db.delete_order(order_id)
#     except OrderNotFound:
#         raise HTTPException(status_code=404, detail="Product not found.")
#     except ValidationError:
#         raise HTTPException(status_code=400, detail="Incorrect input data.")
#     except Exception:
#         logger.error("Error while execute add_order db_method", exc_info=True)
#         raise HTTPException(status_code=500, detail="Internal error.")
#     return "deleted"
