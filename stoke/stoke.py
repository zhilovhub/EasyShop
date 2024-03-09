import datetime
import json
import os
import csv

from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font

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
        """If ``replace`` is true then first delete all products else just add or update by name"""
        if replace:
            await self.product_db.delete_all_products(bot_id)
        for product_dict in json.loads(json_products):
            await self.product_db.upsert_product(
                ProductWithoutId(
                    bot_id=bot_id,
                    **product_dict
                )
            )

    async def export_json(self, bot_id: int) -> str:  # TODO come up with picture
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

        path_to_file = self._generate_path_to_file(bot_id, "json")
        with open(path_to_file, "w", encoding="utf-8") as f:
            json.dump(json_products, f,  indent=4, ensure_ascii=False)

        return path_to_file

    async def import_csv(self, bot_id: int, path_to_file: str, replace: bool) -> None:  # TODO come up with picture
        """If ``replace`` is true then first delete all products else just add or update by name"""
        with open(path_to_file, "r") as f:
            delimiter = csv.Sniffer().sniff(f.read(1024)).delimiter
            f.seek(0)
            reader = csv.reader(f, delimiter=delimiter)
            next(reader)

            products = []
            for row in reader:
                products.append(ProductWithoutId(
                    bot_id=bot_id,
                    name=row[0],
                    description=row[1] if row[1] is not None else "",
                    price=row[2],
                    count=row[3],
                    picture=row[4]
                ))

        if replace:
            await self.product_db.delete_all_products(bot_id)
        for product in products:
            await self.product_db.upsert_product(product)

    async def export_csv(self, bot_id: int) -> str:  # TODO come up with picture
        """Экспорт товаров в виде csv файла"""
        products = await self.product_db.get_all_products(bot_id)

        path_to_file = self._generate_path_to_file(bot_id, "csv")
        with open(path_to_file, "w", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["Название", "Описание", "Цена", "Кол-во", "Картинка"])

            for product in products:
                writer.writerow(
                    [product.name, product.description, product.price, product.count, product.picture]
                )

        return path_to_file

    async def import_xlsx(self, bot_id: int, path_to_file: str, replace: bool) -> None:  # TODO come up with picture
        """If ``replace`` is true then first delete all products else just add or update by name"""
        wb = load_workbook(filename=path_to_file)
        ws = wb.active

        # TODO raise exceptions
        # should be name, description, price, count, picture
        products = []
        for row in list(ws.values)[1:]:
            products.append(ProductWithoutId(
                bot_id=bot_id,
                name=row[0],
                description=row[1] if row[1] is not None else "",
                price=row[2],
                count=row[3],
                picture=row[4]
            ))

        if replace:
            await self.product_db.delete_all_products(bot_id)
        for product in products:
            await self.product_db.upsert_product(product)

    async def export_xlsx(self, bot_id: int) -> str:  # TODO come up with picture
        """Экспорт товаров в виде Excel файла"""
        products = await self.product_db.get_all_products(bot_id)

        wb = Workbook()
        ws = wb.active

        column_names = ["Название", "Описание", "Цена", "Кол-во", "Картинка"]
        column_ind = ['A', 'B', 'C', 'D', 'E']

        ft = Font()
        ft.bold = True

        for ind, name in zip(column_ind, column_names):
            ws[f'{ind}1'] = name
            ws[f'{ind}1'].font = ft

        for ind, product in enumerate(products, start=2):
            ws[f'A{ind}'] = product.name
            ws[f'B{ind}'] = product.description
            ws[f'C{ind}'] = product.price
            ws[f'D{ind}'] = product.count
            ws[f'E{ind}'] = product.picture

        path_to_file = self._generate_path_to_file(bot_id, "xlsx")
        wb.save(path_to_file)

        return path_to_file

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

    def _generate_path_to_file(self, bot_id: int, format: str) -> str:
        return os.environ["FILES_PATH"] + \
                       f"{bot_id}_" + \
                       datetime.datetime.utcnow().strftime("%d%m%y_%H%M%S") + f".{format}"
