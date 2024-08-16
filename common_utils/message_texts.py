from enum import Enum
from typing import Any

from database.config import order_option_db
from database.models.order_model import OrderSchema, OrderItemExtraOption
from database.models.product_model import ProductSchema

from aiogram.utils.formatting import Text, Bold


class MessageTexts(Enum):
    UNKNOWN_ERROR_MESSAGE = """
❗️Произошла ошибка при обработке запроса

🏃‍♂️ Информация моментально подана администраторам, не пройдет и 24 часа, как мы все решим и сделаем продукт для Вас чуточку идеальнее, чем он был до этого момента 🫡

📌 Если что-то срочное или есть какие-то технические вопросы:
СТО: @Ilyyasha
    """  # noqa

    @staticmethod
    async def generate_order_notification_text(
        order: OrderSchema,
        products: list[tuple[ProductSchema, int, list[OrderItemExtraOption] | None]],
        username: str = "@username",
        is_admin: bool = False,
    ) -> dict[str, Any]:
        """
        Translate OrderSchema into the text for notifications
        :param order: the schema of the order
        :param username: the username of the person created an order
        :param is_admin: True if the order is from Admin test web app and False if from custom bot
        :param list products: [(ProductSchema, amount, [OrderItemExtraOption(), ...]), ...]
        """

        products_converted = []
        total_price = 0
        for ind, product_item in enumerate(products, start=1):
            product_schema, amount, extra_options = product_item
            products_converted.append(
                Text(
                    f"{ind}. ",
                    product_schema.convert_to_notification_text(count=amount, used_extra_options=extra_options),
                )
            )
            product_price = product_schema.price
            if extra_options:
                for option in extra_options:
                    if option.price:
                        product_price = option.price
            total_price += product_price * product_item[1]

        products_text = []
        for ind, product_converted in enumerate(products_converted, start=1):  # We can't use "\n".join() here
            products_text.append(product_converted)
            if ind != len(product_converted):
                products_text.append("\n")

        order_options = order.order_options
        order_options_text = Text()
        for order_option_id, value in order_options.items():
            order_option = await order_option_db.get_order_option(order_option_id)
            order_options_text += Text(
                f"{order_option.emoji} {order_option.option_name}: ", Bold(value if value else "Не указано"), "\n"
            )

        if not is_admin:
            result = Text(
                "Ваш заказ ",
                Bold(f"#{order.id}\n\n"),
                "Список товаров: \n\n",
                *products_text,
                "\n\n",
                "Итого: ",
                Bold(f"{total_price}₽\n\n"),
                order_options_text,
                "\n\n " "Статус: ",
                Bold(order.translate_order_status()),
            )
        else:
            result = Text(
                "Новый заказ ",
                Bold(f"#{order.id}\n"),
                "от пользователя ",
                Bold(username),
                "\n\n",
                "Список товаров:\n\n",
                *products_text,
                "\n\n",
                "Итого: ",
                Bold(f"{total_price}₽\n\n"),
                order_options_text,
                "\n\n" "Статус: ",
                Bold(order.translate_order_status()),
            )

        return result.as_kwargs()
