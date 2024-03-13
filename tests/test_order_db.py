import pytest

from database.models.order_model import OrderDao, OrderNotFound
from database.models.product_model import ProductDao
from tests.schemas import product_schema_without_id_1, product_schema_without_id_2, order_schema_1, order_schema_2, \
    product_schema_1, product_schema_2


@pytest.fixture
async def before_add_order(product_db: ProductDao, order_db: OrderDao, before_add_bot) -> None:
    await product_db.add_product(product_schema_without_id_1)
    await product_db.add_product(product_schema_without_id_2)
    await order_db.add_order(order_schema_1)


@pytest.fixture
async def before_add_two_orders(product_db: ProductDao, order_db: OrderDao, before_add_bot) -> None:
    await product_db.add_product(product_schema_without_id_1)
    await product_db.add_product(product_schema_without_id_2)
    await order_db.add_order(order_schema_1)
    await order_db.add_order(order_schema_2)


class TestOrderDb:
    def test_order_text_notification(self) -> None:
        assert order_schema_1.convert_to_notification_text(
            products=[(product_schema_1, 2), (product_schema_2, 1)],
            username="@username",
            is_admin=False
        ) == """Твой заказ <b>#asdF5</b>

Список товаров:

1. <b>Xbox 21000₽ x 2шт</b>
2. <b>Xbox Series X 31000₽ x 1шт</b>
Итого: <b>73000₽</b>

Адрес: <b>Москва</b>
Способ оплаты: <b>Картой онлайн</b>
Комментарий: <b>Позвонтить за 10 минут</b>

Статус: <b>⏳ В обработке</b>"""
        assert order_schema_1.convert_to_notification_text(
            products=[(product_schema_1, 2), (product_schema_2, 1)],
            username="@username",
            is_admin=True
        ) == """Новый заказ <b>#asdF5</b>
от пользователя <b>@username</b>

Список товаров:

1. <b>Xbox 21000₽ x 2шт</b>
2. <b>Xbox Series X 31000₽ x 1шт</b>
Итого: <b>73000₽</b>

Адрес: <b>Москва</b>
Способ оплаты: <b>Картой онлайн</b>
Комментарий: <b>Позвонтить за 10 минут</b>

Статус: <b>⏳ В обработке</b>"""

    async def test_get_order(self, order_db: OrderDao, before_add_order) -> None:
        """OrderDao.get_order"""
        with pytest.raises(OrderNotFound):
            await order_db.get_order("1")

        order = await order_db.get_order(order_schema_1.id)
        assert order == order_schema_1

    async def test_get_all_orders(self, order_db: OrderDao, before_add_two_orders) -> None:
        """OrderDao.get_all_orders"""
        orders = await order_db.get_all_orders(1)
        assert orders[0] == order_schema_1
        assert orders[1] == order_schema_2

    async def test_add_order(self, order_db: OrderDao, before_add_order) -> None:
        """OrderDao.add_order"""
        await order_db.add_order(order_schema_2)
        order = await order_db.get_order(order_schema_2.id)
        assert order_schema_2 == order

    async def test_update_order(self, order_db: OrderDao, before_add_order) -> None:
        """OrderDao.update_order"""
        order_schema_1.comment = "Позвонить за час"
        await order_db.update_order(order_schema_1)
        order = await order_db.get_order(order_schema_1.id)
        assert order.comment == "Позвонить за час"

    async def test_del_order(self, order_db: OrderDao, before_add_order) -> None:
        """OrderDao.delete_order"""
        await order_db.get_order(order_schema_1.id)
        await order_db.delete_order(order_schema_1.id)

        with pytest.raises(OrderNotFound):
            await order_db.get_order(order_schema_1.id)
