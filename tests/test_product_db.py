from datetime import datetime

import pytest

from bot.exceptions import InvalidParameterFormat
from database.models.bot_model import BotDao, BotSchemaWithoutId
from database.models.product_model import ProductDao, ProductSchema, ProductWithoutId, ProductNotFound

BOT_ID = 1

product_schema_without_id_1 = ProductWithoutId(
    bot_id=BOT_ID,
    name="Xbox",
    description="",
    price=21000,
    count=5,
    picture="asd4F.jpg"
)
product_schema_without_id_2 = ProductWithoutId(
    bot_id=BOT_ID,
    name="Xbox Series X",
    description="",
    price=31000,
    count=4,
    picture="sa123.jpg"
)
product_schema_1 = ProductSchema(
    id=1,
    **product_schema_without_id_1.model_dump()
)
product_schema_2 = ProductSchema(
    id=2,
    **product_schema_without_id_2.model_dump()
)

bot_schema_without_id = BotSchemaWithoutId(
    token="1000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA",
    status="a",
    created_at=datetime.utcnow(),
    created_by=1,
    locale=""
)


@pytest.fixture
async def before_add_product(bot_db: BotDao, product_db: ProductDao) -> None:
    await bot_db.add_bot(bot_schema_without_id)
    await product_db.add_product(product_schema_without_id_1)


@pytest.fixture
async def before_add_two_products(bot_db: BotDao, product_db: ProductDao) -> None:
    await bot_db.add_bot(bot_schema_without_id)
    await product_db.add_product(product_schema_without_id_1)
    await product_db.add_product(product_schema_without_id_2)


class TestProductDb:
    def test_product_text_notification(self) -> None:
        assert product_schema_1.convert_to_notification_text(2) == f"<b>Xbox 21000₽ x 2шт</b>"
    
    async def test_get_product(self, product_db: ProductDao, before_add_product) -> None:
        """ProductDao.get_product"""
        with pytest.raises(ProductNotFound):
            await product_db.get_product(product_schema_1.id + 1)

        product = await product_db.get_product(1)
        assert product == product_schema_1

    async def test_get_all_products(self, product_db: ProductDao, before_add_two_products) -> None:
        """ProductDao.get_all_products"""
        products = await product_db.get_all_products(1)
        assert products[0] == product_schema_1
        assert products[1] == product_schema_2

    async def test_add_product(self, product_db: ProductDao, before_add_product) -> None:
        """ProductDao.add_product"""
        with pytest.raises(InvalidParameterFormat):
            await product_db.add_product(product_schema_1)

        product_id = await product_db.add_product(product_schema_without_id_2)
        product = await product_db.get_product(product_id)
        assert product_schema_2 == product

    async def test_update_product(self, product_db: ProductDao, before_add_product) -> None:
        """ProductDao.update_product"""
        product_schema_1.price = 19000
        await product_db.update_product(product_schema_1)
        product = await product_db.get_product(product_schema_1.id)
        assert product.price == 19000

    async def test_del_product(self, product_db: ProductDao, before_add_product) -> None:
        """ProductDao.delete_product"""
        await product_db.get_product(product_schema_1.id)
        await product_db.delete_product(product_schema_1.id)

        with pytest.raises(ProductNotFound):
            await product_db.get_product(product_schema_1.id)
