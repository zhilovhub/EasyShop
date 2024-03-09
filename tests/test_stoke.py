import json
import os
from datetime import datetime
from openpyxl import load_workbook

import pytest

from database.models.bot_model import BotDao, BotSchemaWithoutId
from database.models.product_model import ProductDao, ProductWithoutId, ProductSchema
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
product_schema_without_id_3 = ProductWithoutId(
    bot_id=BOT_ID,
    name="Xbox Series XXX",
    description="",
    price=55000,
    count=122,
    picture="fghdf.jpg"
)
product_schema_2 = ProductSchema(
    id=4,
    **product_schema_without_id_2.model_dump()
)
product_schema_3 = ProductSchema(
    id=3,
    **product_schema_without_id_3.model_dump()
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
    async def test_import_json(self, stoke: Stoke, product_db: ProductDao, before_add_two_products) -> None:
        """Stoke.import_json"""
        await stoke.import_json(
            BOT_ID,
            json.dumps([product_schema_without_id_3.model_dump(exclude={"bot_id"})]),
            replace=True  # with replace True
        )
        products = await product_db.get_all_products(BOT_ID)
        assert len(products) == 1
        assert products[0] == product_schema_3

        product_schema_without_id_3.count = 50
        await stoke.import_json(
            BOT_ID,
            json.dumps([
                product_schema_without_id_2.model_dump(exclude={"bot_id"}),
                product_schema_without_id_3.model_dump(exclude={"bot_id"})
            ]),
            replace=False  # with replace False
        )
        product_schema_3.count = 50
        products = await product_db.get_all_products(BOT_ID)
        assert len(products) == 2
        assert products[0] == product_schema_3 and products[1] == product_schema_2
        product_schema_3.count = 122

    async def test_export_json(self, stoke: Stoke, before_add_two_products) -> None:
        """Stoke.export_json"""
        json_products_in_bytes = await stoke.export_json(bot_id=BOT_ID)
        assert json_products_in_bytes.decode(encoding="utf-8") == \
               open("tests/raw_files/export_json_test.json", "r", encoding="utf-8").read()

    async def test_import_xlsx(self, stoke: Stoke, product_db: ProductDao, before_add_two_products) -> None:
        """Stoke.import_xlsx"""
        await stoke.import_xlsx(
            BOT_ID,
            "tests/raw_files/import_xlsx_1_file_test.xlsx",
            replace=True  # with replace True
        )
        products = await product_db.get_all_products(BOT_ID)
        assert len(products) == 1
        assert products[0] == product_schema_3

        product_schema_without_id_3.count = 50
        await stoke.import_xlsx(
            BOT_ID,
            "tests/raw_files/import_xlsx_2_files_test.xlsx",
            replace=False  # with replace False
        )
        product_schema_3.count = 50
        products = await product_db.get_all_products(BOT_ID)
        assert len(products) == 2
        assert products[0] == product_schema_3 and products[1] == product_schema_2

    async def test_export_xlsx(self, stoke: Stoke, before_add_two_products) -> None:
        """Stoke.export_xlsx"""
        path_to_file = await stoke.export_xlsx(BOT_ID)
        wb = load_workbook(filename=path_to_file, read_only=True)
        ws = wb.active

        excepted_products = [product_schema_without_id_1, product_schema_without_id_2]
        for excepted_product, row in zip(excepted_products, list(ws.values)[1:]):
            assert ProductWithoutId(
                bot_id=BOT_ID,
                name=row[0],
                description=row[1] if row[1] is not None else "",
                price=row[2],
                count=row[3],
                picture=row[4]
            ) == excepted_product

        wb.close()
        os.remove(path_to_file)

    async def test_get_product_count(self, stoke: Stoke, before_add_two_products) -> None:
        """Stoke.get_product_count"""
        assert await stoke.get_product_count(1) == 23 and await stoke.get_product_count(-20) == 0

    async def test_update_product_count(self, stoke: Stoke, product_db: ProductDao, before_add_two_products) -> None:
        """Stoke.update_product_count"""
        product_id = 1
        count = 345
        await stoke.update_product_count(product_id, count)
        assert (await product_db.get_product(product_id)).count == count
