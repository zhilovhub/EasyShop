import asyncio
import json
import os

from aiogram.types import BufferedInputFile

from database.models.models import Database


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

    def import_json(self, product_schema: None) -> None:
        pass

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

    def get_product_count(self, product_id: int) -> int:
        pass

    def update_product_count(self, product_id: int, new_count: int) -> None:
        pass
