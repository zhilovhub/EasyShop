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
        self.database = database

    def import_json(self, product_schema: None) -> None:
        pass

    def export_json(self) -> dict:
        pass

    def import_xsl(self, product_schema: None) -> None:
        pass

    def export_xsl(self) -> dict:
        pass

    def get_product_count(self, product_id: int) -> int:
        pass

    def update_product_count(self, product_id: int, new_count: int) -> None:
        pass
