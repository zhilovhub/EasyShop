from enum import Enum
from aiogram.utils.formatting import Text, Bold
from typing import List
from database.models.product_model import ProductSchema


class CustomMessageTexts(Enum):
    BOT_ADDED_TO_CHANNEL_MESSAGE = (
        "Ваш бот @{} был <b>добавлен</b> в канал @{}\n\n"
        "⚙ Для настройки взаимодействия с каналами нажмите на кнопку <b>Мои Каналы</b>"
    )

    BOT_REMOVED_FROM_CHANNEL_MESSAGE = "Ваш бот @{} был <b>удалён</b> из канала @{}"

    ERROR_IN_CREATING_INVOICE = "Произошла ошибка при создании платежа, администратор магазина уведомлен."

    @staticmethod
    def generate_not_enough_in_stock(products: List[ProductSchema], order_id):
        result = Text("Чтобы выполнить заказ ", Bold(order_id), " на Вашем складе не хватает следующих товаров:\n\n")
        for product in products:
            result += Text(Bold(product.name), " артикул ", Bold(product.article) + "\n")
        return result.as_kwargs()

    @staticmethod
    def generate_stock_info_to_refill(products_to_refill: List[ProductSchema], order_id):
        result = Text("После заказа ", Bold(order_id), " закончатся следующие товары:\n\n")
        for product in products_to_refill:
            result += Text(Bold(product.name), " артикул ", Bold(product.article) + "\n")
        return result.as_kwargs()

    @staticmethod
    def show_product_review_info(mark: int, review_text: str, product_name: str):
        return f"Новый отзыв на продукт <b>{product_name}</b>\n\n" f"Оценка - {mark}\n\n" f"Отзыв - {review_text}"
