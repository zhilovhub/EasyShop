import json

from database.models.models import Database
from database.models.product_model import ProductNotFound, ProductWithoutId


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


@singleton
class Stoke:
    """Модуль склада"""

    def __init__(self, database: Database) -> None:
        self.product_db = database.get_product_db()

    async def import_json(self, bot_id: int, json_products: str, replace: bool) -> None:  # TODO come up with picture
        """If ``replace`` is true then replace all products else just add or update by name"""
        if replace:
            await self.product_db.delete_all_products(bot_id)
        for product_dict in json.loads(json_products):
            await self.product_db.upsert_product(
                ProductWithoutId(
                    bot_id=bot_id,
                    **product_dict
                )
            )

    async def export_json(self, bot_id: int) -> bytes:
        """Экспорт товаров в виде json файла"""
        products = await self.product_db.get_all_products(bot_id)
        json_products = []
        for product in products:
            json_products.append({
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "count": product.count
            })
        return bytes(json.dumps(json_products, indent=4, ensure_ascii=False), encoding="utf-8")

    def import_xlsx(self, product_schema: None) -> None:
        pass

    def export_xlsx(self, bot_id: int) -> dict:
        pass

    async def get_product_count(self, product_id: int) -> int:
        """Возвращает количество товара на складе"""
        try:
            return (await self.product_db.get_product(product_id)).count
        except ProductNotFound:
            return 0

    async def update_product_count(self, product_id: int, new_count: int) -> None:
        """Обновляет количетсво товара на складе"""
        product = await self.product_db.get_product(product_id)
        product.count = new_count
        await self.product_db.update_product(product)
