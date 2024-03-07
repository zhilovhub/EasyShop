from datetime import datetime

import pytest

from database.models.bot_model import BotDao, BotSchemaWithoutId
from database.models.product_model import ProductDao, ProductWithoutId
from stoke.stoke import Stoke

BOT_ID = 1

product_schema_without_id_1 = ProductWithoutId(
    bot_id=BOT_ID,
    name="Xbox",
    description="",
    price=21000,
    count=23,
    picture="asd4F.jpg"
)
product_schema_without_id_2 = ProductWithoutId(
    bot_id=BOT_ID,
    name="Xbox Series X",
    description="",
    price=31000,
    count=12,
    picture="sa123.jpg"
)

bot_schema_without_id = BotSchemaWithoutId(
    token="1000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA",
    status="a",
    created_at=datetime.utcnow(),
    created_by=1,
    locale=""
)


@pytest.fixture
async def before_add_two_products(bot_db: BotDao, product_db: ProductDao) -> None:
    await bot_db.add_bot(bot_schema_without_id)
    await product_db.add_product(product_schema_without_id_1)
    await product_db.add_product(product_schema_without_id_2)


class TestStoke:
    async def test_export_json(self, stoke: Stoke, before_add_two_products) -> None:
        json_products_in_bytes = await stoke.export_json(bot_id=BOT_ID)
        assert json_products_in_bytes.decode(encoding="utf-8") == \
               open("tests/raw_files/export_json_test.json", "r", encoding="utf-8").read()
