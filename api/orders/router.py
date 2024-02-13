from database.models.order_model import OrderSchema, OrderWithoutId, OrderDao, OrderNotFound
from ..main import db_engine, app, logger
from fastapi import HTTPException
from pydantic import ValidationError


PATH = "/api/orders"
db = db_engine.get_order_dao()


@app.get(PATH + "/get_all_orders/{token}", tags=['orders'])
async def get_all_orders_api(token: str) -> list[OrderSchema]:
    token = token.replace('_', ':')
    try:
        orders = await db.get_all_orders(token)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Incorrect input data.")
    except Exception:
        logger.error("Error while execute get_all_orders db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return orders


@app.get(PATH + "/get_order/{token}/{order_id}", tags=['orders'])
async def get_order_api(token: str, order_id: str) -> OrderSchema:
    token = token.replace('_', ':')
    try:
        order = await db.get_order(token, order_id)
    except OrderNotFound:
        raise HTTPException(status_code=404, detail="Product not found.")
    except ValidationError:
        raise HTTPException(status_code=400, detail="Incorrect input data.")
    except Exception:
        logger.error("Error while execute get_order db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return order


@app.post(PATH + "/add_order", tags=['orders'])
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


@app.post(PATH + "/update_order", tags=['orders'])
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


@app.delete(PATH + "/delete_order/{token}/{order_id}", tags=['orders'])
async def delete_order_api(bot_token: str, order_id: str) -> str:
    bot_token = bot_token.replace('_', ':')
    try:
        await db.delete_order(bot_token, order_id)
    except OrderNotFound:
        raise HTTPException(status_code=404, detail="Product not found.")
    except ValidationError:
        raise HTTPException(status_code=400, detail="Incorrect input data.")
    except Exception:
        logger.error("Error while execute add_order db_method", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error.")
    return "deleted"
