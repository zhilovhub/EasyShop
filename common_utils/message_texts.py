from enum import Enum
from typing import Any

from aiogram.utils.formatting import Bold, Text

from database.config import order_option_db
from database.enums import UserLanguageValues, UserLanguageEmoji
from database.models.order_model import OrderSchema, OrderItemExtraOption
from database.models.product_model import ProductSchema


class MessageTexts(Enum):
    UNKNOWN_ERROR_MESSAGE = """
❗️Произошла ошибка при обработке запроса

🏃‍♂️ Информация моментально подана администраторам, не пройдет и 24 часа, как мы все решим и сделаем продукт для Вас чуточку идеальнее, чем он был до этого момента 🫡

📌 Если что-то срочное или есть какие-то технические вопросы:
СТО: @Ilyyasha
    """  # noqa

    @staticmethod
    def get_first_select_language_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(
                    "Выбран язык по умолчанию ",
                    Bold(f"({UserLanguageEmoji.RUSSIAN.value})"),
                    "\n\n👇 Выберите доступный в боте язык",
                )
            case UserLanguageValues.HEBREW:
                return Text(
                    "שפת ברירת המחדל נבחרה",
                    Bold(f"({UserLanguageEmoji.HEBREW.value})"),
                    "\n\n👇 בחר שפה זמינה בבוט",
                )
            case UserLanguageValues.ENGLISH | _:
                return Text(
                    "Default language selected ",
                    Bold(f"({UserLanguageEmoji.ENGLISH.value})"),
                    "\n\n👇 Select the language available in the bot",
                )

    @staticmethod
    async def generate_order_notification_text(
        order: OrderSchema,
        products: list[tuple[ProductSchema, int, list[OrderItemExtraOption] | None]],
        username: str = "@username",
        is_admin: bool = False,
        lang: UserLanguageValues = UserLanguageValues.RUSSIAN,
    ) -> dict[str, Any]:
        """
        Translate OrderSchema into the text for notifications
        :param order: the schema of the order
        :param username: the username of the person created an order
        :param is_admin: True if the order is from Admin test web app and False if from custom bot
        :param list products: [(ProductSchema, amount, [OrderItemExtraOption(), ...]), ...]
        :param lang: text language
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

        match lang:
            case UserLanguageValues.RUSSIAN:
                your_order = "Ваш заказ "
                new_order = "Новый заказ "
                from_user = "от пользователя "
                products_list = "Список товаров"
                summary = "Итого"
                status = "Статус"
            case UserLanguageValues.HEBREW:
                your_order = "ההזמנה שלך "
                new_order = "ההזמנה שלך "
                from_user = "מהמשתמש "
                products_list = "רשימת מוצרים"
                summary = "סך הכל"
                status = "סטטוס"
            case UserLanguageValues.ENGLISH | _:
                your_order = "Your order "
                new_order = "New order "
                from_user = "from user "
                products_list = "Products list"
                summary = "Summary"
                status = "Status"

        if not is_admin:
            result = Text(
                your_order,
                Bold(f"#{order.id}\n\n"),
            )
        else:
            result = Text(
                new_order,
                Bold(f"#{order.id}\n"),
                from_user,
                Bold(username),
                "\n\n",
            )

        result += Text(
            f"{products_list}: \n\n",
            *products_text,
            "\n\n",
            f"{summary}: ",
            Bold(f"{total_price}₽\n\n"),
        )
        result += order_options_text
        result += Text(
            f"\n\n {status}: ",
            Bold(order.translate_order_status(lang)),
        )

        return result.as_kwargs()
