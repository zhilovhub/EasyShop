# import pytest
#
# from database.exceptions import InvalidParameterFormat
# from database.models.product_model import ProductDao, ProductNotFound
# from tests.schemas import product_schema_without_id_1, product_schema_without_id_2, product_schema_1, \
#     product_schema_2, BOT_ID
#
#
# @pytest.fixture
# async def before_add_product(product_db: ProductDao, before_add_bot) -> None:
#     await product_db.add_product(product_schema_without_id_1)
#
#
# @pytest.fixture
# async def before_add_two_products(product_db: ProductDao, before_add_bot) -> None:
#     await product_db.add_product(product_schema_without_id_1)
#     await product_db.add_product(product_schema_without_id_2)
#
#
# class TestProductDb:
#     def test_product_text_notification(self) -> None:
#         assert product_schema_1.convert_to_notification_text(2) == f"<b>Xbox 21000₽ x 2шт</b>"
#
#     async def test_get_product(self, product_db: ProductDao, before_add_product) -> None:
#         """ProductDao.get_product"""
#         with pytest.raises(ProductNotFound):
#             await product_db.get_product(product_schema_1.id + 1)
#
#         product = await product_db.get_product(1)
#         assert product == product_schema_1
#
#     async def test_get_all_products(self, product_db: ProductDao, before_add_two_products) -> None:
#         """ProductDao.get_all_products"""
#         products = await product_db.get_all_products(1)
#         assert products[0] == product_schema_1
#         assert products[1] == product_schema_2
#
#     async def test_add_product(self, product_db: ProductDao, before_add_product) -> None:
#         """ProductDao.add_product"""
#         with pytest.raises(InvalidParameterFormat):
#             await product_db.add_product(product_schema_1)
#
#         product_id = await product_db.add_product(product_schema_without_id_2)
#         product = await product_db.get_product(product_id)
#         assert product_schema_2 == product
#
#     async def test_upsert_product(self, product_db: ProductDao, before_add_product) -> None:
#         """ProductDao.upsert_product"""
#         product_schema_1.count = 4
#         await product_db.upsert_product(product_schema_1)
#         await product_db.upsert_product(product_schema_without_id_2)
#         updated_product = await product_db.get_product(product_schema_1.id)
#         assert updated_product.count == 4
#
#         # plus because upsert always increments id
#         inserted_product = await product_db.get_product(product_schema_2.id + 1)
#         product_schema_2.id = product_schema_2.id + 1
#         assert inserted_product == product_schema_2
#
#     async def test_update_product(self, product_db: ProductDao, before_add_product) -> None:
#         """ProductDao.update_product"""
#         product_schema_1.price = 19000
#         await product_db.update_product(product_schema_1)
#         product = await product_db.get_product(product_schema_1.id)
#         assert product.price == 19000
#
#     async def test_del_product(self, product_db: ProductDao, before_add_product) -> None:
#         """ProductDao.delete_product"""
#         await product_db.get_product(product_schema_1.id)
#         await product_db.delete_product(product_schema_1.id)
#
#         with pytest.raises(ProductNotFound):
#             await product_db.get_product(product_schema_1.id)
#
#     async def test_delete_all_products(self, product_db: ProductDao, before_add_two_products) -> None:
#         """ProductDao.delete_all_products"""
#         await product_db.delete_all_products(BOT_ID)
#         products = await product_db.get_all_products(BOT_ID)
#
#         assert len(products) == 0
