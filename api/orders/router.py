from datetime import datetime
import random
import string
from typing import Any

import aiohttp

from pydantic import ValidationError, BaseModel

from fastapi import APIRouter, Depends, Header

from api.utils import (
    check_admin_authorization,
    HTTPBadRequestError,
    HTTPInternalError,
    RESPONSES_DICT,
    HTTPUnauthorizedError,
    HTTPBotNotFoundError,
)

from common_utils.config import custom_telegram_bot_settings
from common_utils.order_utils.order_type import OrderType
from common_utils.exceptions.local_api_exceptions import LocalAPIException

from database.config import order_db
from database.models.order_model import OrderNotFoundError, OrderSchema

from logs.config import api_logger, extra_params

PATH = "/orders"
router = APIRouter(
    prefix=PATH,
    tags=["orders"],
    responses=RESPONSES_DICT,
)


@router.get("/generate_order_id")
async def generate_order_id_api() -> str:
    """
    :return: The unique order id for order
    """
    date = datetime.now().strftime("%d%m%y")
    random_string = "".join(random.sample(string.digits + string.ascii_letters, 5))
    order_id = date + random_string

    try:
        await order_db.get_order(order_id)
    except OrderNotFoundError:
        api_logger.debug(
            f"order_id={random_string}: order_id has been generated", extra=extra_params(order_id=random_string)
        )
        return random_string

    api_logger.warning("generated order_id already exist, regenerating...")
    await generate_order_id_api()


@router.get("/get_all_orders/{bot_id}")
async def get_all_orders_api(bot_id: int, authorization_data: str = Header()) -> list[OrderSchema]:
    """
    :raises HTTPException:
    :raises HTTPBadRequestError:
    :raises HTTPInternalError:
    """
    await check_admin_authorization(bot_id, authorization_data)
    try:
        orders = await order_db.get_all_orders(bot_id)
    except ValidationError as ex:
        api_logger.error(f"bot_id={bot_id}: validation error", extra=extra_params(bot_id=bot_id), exc_info=ex)
        raise HTTPBadRequestError(detail_message="Incorrect input data.", ex_msg=str(ex))
    except Exception as e:
        api_logger.error(
            f"bot_id={bot_id}: Error while execute get_all_orders db_method",
            extra=extra_params(bot_id=bot_id),
            exc_info=e,
        )
        raise HTTPInternalError

    api_logger.debug(f"bot_id={bot_id}: has {len(orders)} orders -> {orders}", extra=extra_params(bot_id=bot_id))

    return orders


@router.post("/add_order")
async def add_order_api(new_order: OrderSchema = Depends(), authorization_data: str = Header()) -> str:
    """
    :raises HTTPException:
    :raises HTTPInternalError:
    """
    await check_admin_authorization(new_order.bot_id, authorization_data)
    try:
        new_order.ordered_at = new_order.ordered_at.replace(tzinfo=None)
        await order_db.add_order(new_order)

        api_logger.debug(
            f"bot_id={new_order.bot_id}: order {new_order} has been added",
            extra=extra_params(bot_id=new_order.bot_id, order_id=new_order.id),
        )
    except Exception as e:
        api_logger.error(
            f"Error while execute add_order db_method with {new_order}",
            extra=extra_params(bot_id=new_order.bot_id, order_id=new_order.id),
            exc_info=e,
        )
        raise HTTPInternalError

    return "success"


class OrderData(BaseModel):
    bot_id: int
    raw_items: dict
    raw_order_options: dict[int, Any]
    ordered_at: datetime
    query_id: str | None = None
    from_user: int | None = None
    order_type: OrderType | None = None


class SendOrderDataResponse(BaseModel):
    invoice_url: str | None = None


@router.post("/send_order_data_to_bot")
async def send_order_data_to_bot_api(
    order_data: OrderData, authorization_data: str = Header()
) -> SendOrderDataResponse:
    """
    :raises HTTPInternalError:
    """
    try:
        await check_admin_authorization(order_data.bot_id, authorization_data, custom_bot_validate=False)
        order_data.order_type = OrderType.MAIN_BOT_TEST_ORDER.value
    except HTTPUnauthorizedError:
        try:
            await check_admin_authorization(order_data.bot_id, authorization_data, custom_bot_validate=True)
            order_data.order_type = OrderType.CUSTOM_BOT_ORDER.value
        except:
            api_logger.debug("custom bot user unauthorized")
            raise
    except (HTTPUnauthorizedError, HTTPBotNotFoundError) as e:
        raise e
    try:
        api_logger.debug(f"get new order data from web_app: {order_data}")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"http://{custom_telegram_bot_settings.WEBHOOK_LOCAL_API_URL_HOST}:"
                f"{custom_telegram_bot_settings.WEBHOOK_LOCAL_API_PORT}"
                f"/send_web_app_data_to_bot/{order_data.bot_id}",
                data=order_data.model_dump_json(),
            ) as response:
                if response.status != 200:
                    api_logger.error(
                        f"Local API returned {response.status} status code " f"with body {await response.text()}"
                    )
                    raise LocalAPIException
                invoice_url = (await response.json())["invoice_url"]
    except LocalAPIException:
        raise HTTPInternalError(detail_message="Local Api error")
    except Exception as e:
        api_logger.error(
            f"Error while execute send_order_data_to_bot api with {order_data}",
            extra=extra_params(bot_id=order_data.bot_id),
            exc_info=e,
        )
        raise HTTPInternalError

    return SendOrderDataResponse(invoice_url=invoice_url)
