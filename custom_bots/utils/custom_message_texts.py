from enum import Enum
from aiogram.utils.formatting import Text, Bold, Underline, Italic
from typing import List

from database.models.product_model import ProductSchema

from database.enums import UserLanguageValues, UserLanguageEmoji


class CustomMessageTexts(Enum):
    @staticmethod
    def get_bot_added_to_channel_message(lang: UserLanguageValues, bot_username: str, channel_username: str) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(
                    "Ваш бот ",
                    Bold(f"@{bot_username}"),
                    " был ",
                    Underline("добавлен"),
                    " в канал ",
                    Bold(f"@{channel_username}\n\n"),
                    "⚙ Для настройки взаимодействия с каналами нажмите на кнопку ",
                    Bold("Мои Каналы"),
                )
            case UserLanguageValues.HEBREW:
                return Text(
                    "הבוט שלך ",
                    Bold(f" @{bot_username}"),
                    " היה ",
                    Underline("נוסף"),
                    " לערוץ ",
                    Bold(f"@{channel_username}\n\n"),
                    "⚙כדי להגדיר אינטראקציה עם ערוצים, לחץ על הכפתור",
                    Bold("הערוצים שלי"),
                )
            case UserLanguageValues.ENGLISH | _:
                return Text(
                    "Your bot ",
                    Bold(f"@{bot_username}"),
                    " was ",
                    Underline("added"),
                    " into the channel ",
                    Bold(f"@{channel_username}\n\n"),
                    "⚙ To set up interaction with channels, click on the button ",
                    Bold("My Channels"),
                )

    @staticmethod
    def get_removed_from_channel_message(lang: UserLanguageValues, bot_username: str, channel_username: str) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(
                    "Ваш бот ",
                    Bold(f"@{bot_username}"),
                    " был ",
                    Underline("удалён"),
                    " из канала ",
                    Bold(f"@{channel_username}"),
                )
            case UserLanguageValues.HEBREW:
                return Text(
                    "הבוט שלך ",
                    Bold(f"@{bot_username}"),
                    "היה",
                    Underline("הוסר"),
                    "מהערוץ ",
                    Bold(f"@{channel_username}"),
                )
            case UserLanguageValues.ENGLISH | _:
                return Text(
                    "Your bot ",
                    Bold(f"@{bot_username}"),
                    "was",
                    Underline("deleted"),
                    " from the channel",
                    Bold(f"@{channel_username}"),
                )

    @staticmethod
    def get_bot_rights_channel_message(lang: UserLanguageValues, bot_username: str, channel_username: str) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(
                    "Права бота ",
                    Bold(f"@{bot_username}"),
                    " в канале ",
                    Bold(f"@{channel_username}"),
                    " изменены:\n\n",
                )
            case UserLanguageValues.HEBREW:
                return Text(
                    " זכויות בוט ", Bold(f"@{bot_username}"), " בערוץ ", Bold(f"@{channel_username}"), " השתנה:\n\n"
                )
            case UserLanguageValues.ENGLISH:
                return Text(
                    "Bot rights ",
                    Bold(f"@{bot_username}"),
                    " in channel ",
                    Bold(f"@{channel_username}"),
                    " changed:\n\n",
                )

    @staticmethod
    def get_error_in_creating_invoice_text(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Произошла ошибка при создании платежа, администратор магазина уведомлен")
            case UserLanguageValues.HEBREW:
                return Text("אירעה שגיאה בעת יצירת התשלום, מנהל החנות קיבל הודעה")
            case UserLanguageValues.ENGLISH | _:
                return Text("An error occurred when creating the payment, the store administrator has been notified")

    @staticmethod
    def get_inline_not_found_texts(lang: UserLanguageValues) -> dict:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return {
                    "title": "Товары не найдены.",
                    "description": "По указанному запросу не было найдено ни одного товара в базе бота.",
                }
            case UserLanguageValues.HEBREW:
                return {"title": "לא נמצאו מוצרים.", "description": "על פי בקשה זו, לא נמצא מוצר אחד בבסיס הבוט."}
            case UserLanguageValues.ENGLISH | _:
                return {
                    "title": "No products found.",
                    "description": "No product was found in the bot database for the specified query.",
                }

    @staticmethod
    def get_pre_checkout_unknown_error(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Произошла неопознанная ошибка, мы уже работаем над этим."
            case UserLanguageValues.HEBREW:
                return "אירעה שגיאה לא מזוהה, אנחנו כבר עובדים על זה."
            case UserLanguageValues.ENGLISH | _:
                return "An unidentified error has occurred, we are already working on it."

    @staticmethod
    def get_lang_already_set(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Язык уже установлен"
            case UserLanguageValues.HEBREW:
                return "השפה כבר מותקנת"
            case UserLanguageValues.ENGLISH | _:
                return "Language already set"

    @staticmethod
    def get_lang_set(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Язык изменен"
            case UserLanguageValues.HEBREW:
                return "השפה השתנתה"
            case UserLanguageValues.ENGLISH | _:
                return "Language changed"

    @staticmethod
    def get_success_payment_message(lang: UserLanguageValues, pay_id: int) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(f"✅ Оплата прошла успешно. [payment_id: {pay_id}]")
            case UserLanguageValues.HEBREW:
                return Text(f"✅ התשלום היה מוצלח. [payment_id: {pay_id}]")
            case UserLanguageValues.ENGLISH | _:
                return Text("✅ The payment was successful. [payment_id: {pay_id}]")

    @staticmethod
    def get_select_language_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(
                    "Текущий язык ",
                    Bold(f"({UserLanguageEmoji.RUSSIAN.value})"),
                    "\n\n👇 Для смены языка нажмите на кнопки ниже.",
                )
            case UserLanguageValues.HEBREW:
                return Text(
                    "שפה נוכחית ",
                    Bold(f"({UserLanguageEmoji.HEBREW.value})"),
                    "\n\n👇 כדי לשנות את השפה, לחץ על הכפתורים למטה.",
                )
            case UserLanguageValues.ENGLISH | _:
                return Text(
                    "Current language ",
                    Bold(f"({UserLanguageEmoji.ENGLISH.value})"),
                    "\n\n👇 To change the language, click on the buttons below.",
                )

    @staticmethod
    def get_bot_not_init_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("⚙️ Бот еще не инициализирован.")
            case UserLanguageValues.HEBREW:
                return Text("⚙️ הבוט עדיין לא מאותחל.")
            case UserLanguageValues.ENGLISH | _:
                return Text("⚙️ The bot has not been initialized yet.")

    @staticmethod
    def get_product_page_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(Bold("👇 Страничка товара:"))
            case UserLanguageValues.HEBREW:
                return Text(Bold("👇 דף מוצר:"))
            case UserLanguageValues.ENGLISH | _:
                return Text(Bold("👇 Product page:"))

    @staticmethod
    def get_shop_page_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(Bold("👇 Наш магазин:"))
            case UserLanguageValues.HEBREW:
                return Text(Bold("👇 שלנו חנות:"))
            case UserLanguageValues.ENGLISH | _:
                return Text(Bold("👇 Our store:"))

    @staticmethod
    def get_shop_button_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(Bold("Кнопка для входа в магазин 👇"))
            case UserLanguageValues.HEBREW:
                return Text(Bold("כפתור כניסה לחנות 👇"))
            case UserLanguageValues.ENGLISH | _:
                return Text(Bold("The button to enter the store 👇"))

    @staticmethod
    def get_not_enough_in_stock_err_message(lang: UserLanguageValues, product_name: str) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(
                    "📦🚫\nК сожалению на складе недостаточно товара:\n",
                    Bold(product_name),
                    "\nдля выполнения Вашего заказа.",
                )
            case UserLanguageValues.HEBREW:
                return Text(
                    "📦🚫\n",
                    " מחשב למרבה הצער אין מספיק מוצר במלאי:",
                    "\n",
                    Bold(product_name),
                    "\n",
                    "כדי למלא את ההזמנה שלך.",
                )
            case UserLanguageValues.ENGLISH | _:
                return Text(
                    "📦🚫\n Unfortunately there is not enough product:\n",
                    Bold(product_name),
                    "\nin stock to fulfill your order.",
                )

    @staticmethod
    def get_order_creation_err_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("🚫 Произошла ошибка при создании заказа, администраторы уведомлены.")
            case UserLanguageValues.HEBREW:
                return Text("🚫 אירעה שגיאה בעת יצירת ההזמנה, מנהלי מערכת קיבלו הודעה.")
            case UserLanguageValues.ENGLISH | _:
                return Text("🚫 An error occurred when creating an order, administrators have been notified.")

    @staticmethod
    def get_ask_question_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("📨 Вы можете отправить свой вопрос по заказу, отправив любое сообщение боту")
            case UserLanguageValues.HEBREW:
                return Text("📨 אתה יכול לשלוח את שאלתך בהזמנה על ידי שליחת כל הודעה לבוט")
            case UserLanguageValues.ENGLISH | _:
                return Text("📨 You can send your question on the order by sending any message to the bot")

    @staticmethod
    def get_select_product_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Выберите товар 🏷")
            case UserLanguageValues.HEBREW:
                return Text("בחר פריט 🏷")
            case UserLanguageValues.ENGLISH | _:
                return Text("Select a product 🏷")

    @staticmethod
    def get_review_product_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Оцените качество товаров ✔️")
            case UserLanguageValues.HEBREW:
                return Text("דרג את איכות הסחורה ✔️")
            case UserLanguageValues.ENGLISH | _:
                return Text("Rate the quality of the goods ✔️")

    @staticmethod
    def get_send_review_canceled_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Отправка отзыва отменена ✖️")
            case UserLanguageValues.HEBREW:
                return Text("שליחת משוב בוטלה ✖️")
            case UserLanguageValues.ENGLISH | _:
                return Text("Sending a review has been canceled ✖️")

    @staticmethod
    def get_review_score_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Чтобы оставить оценку, нажмите на кнопку ниже 👇")
            case UserLanguageValues.HEBREW:
                return Text("כדי להשאיר ציון, לחץ על הכפתור למטה 👇")
            case UserLanguageValues.ENGLISH | _:
                return Text("To leave a rating, click on the button below 👇")

    @staticmethod
    def get_review_thx_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Спасибо за отзыв 📬")
            case UserLanguageValues.HEBREW:
                return Text("תודה על המשוב 📬")
            case UserLanguageValues.ENGLISH | _:
                return Text("Thanks for the feedback. 📬")

    @staticmethod
    def get_review_comment_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Напишите комментарий к вашему отзыву 📨")
            case UserLanguageValues.HEBREW:
                return Text("כתוב תגובה למשוב שלך 📨")
            case UserLanguageValues.ENGLISH | _:
                return Text("Write a comment to your review 📨")

    @staticmethod
    def get_order_change_err_message(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "🚫 Ошибка при работе с заказом, возможно статус уже изменился"
            case UserLanguageValues.HEBREW:
                return "🚫 שגיאה בעבודה עם ההזמנה, אולי הסטטוס כבר השתנה"
            case UserLanguageValues.ENGLISH | _:
                return "🚫 Error when working with the order, the status may have already changed"

    @staticmethod
    def get_review_already_err_message(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "🚫 Вы уже оставили отзыв на этот продукт!"
            case UserLanguageValues.HEBREW:
                return "🚫 כבר השארת ביקורת על מוצר זה!"
            case UserLanguageValues.ENGLISH | _:
                return "🚫 You have already left a review for this product!"

    @staticmethod
    def get_status_already_err_message(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "🚫 Этот статус уже выставлен"
            case UserLanguageValues.HEBREW:
                return "🚫 מעמד זה כבר נחשף"
            case UserLanguageValues.ENGLISH | _:
                return "🚫 This status has already been set"

    @staticmethod
    def get_order_change_maybe_deleted_err_message(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "🚫 Ошибка при работе с заказом, возможно заказ был удалён"
            case UserLanguageValues.HEBREW:
                return "🚫 שגיאה בעבודה עם ההזמנה, אולי ההזמנה נמחקה"
            case UserLanguageValues.ENGLISH | _:
                return "🚫 Error when working with the order, the order may have been deleted"

    @staticmethod
    def get_work_only_in_channel_text(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Работает только в канале"
            case UserLanguageValues.HEBREW:
                return "עובד רק בערוץ"
            case UserLanguageValues.ENGLISH | _:
                return "Only works in the channel"

    @staticmethod
    def get_contest_finished_text(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Конкурс уже завершен"
            case UserLanguageValues.HEBREW:
                return "התחרות כבר הסתיימה"
            case UserLanguageValues.ENGLISH | _:
                return "The competition has already been completed"

    @staticmethod
    def get_contest_join_text(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Теперь вы участвуете в конкурсе"
            case UserLanguageValues.HEBREW:
                return "עכשיו אתה נכנס לתחרות"
            case UserLanguageValues.ENGLISH | _:
                return "Now you are participating in the competition"

    @staticmethod
    def get_contest_already_joined_text(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Вы уже участвуете в этом конкурсе"
            case UserLanguageValues.HEBREW:
                return "אתה כבר משתתף בתחרות זו"
            case UserLanguageValues.ENGLISH | _:
                return "You are already participating in this competition"

    @staticmethod
    def get_order_removed_by_admin(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Заказ удалён администратором"
            case UserLanguageValues.HEBREW:
                return "ההזמנה הוסרה על ידי מנהל המערכת"
            case UserLanguageValues.ENGLISH | _:
                return "Order was deleted by admin"

    @staticmethod
    def get_cant_send_question(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Не удалось отправить Ваш вопрос. Администраторы уже уведомлены"
            case UserLanguageValues.HEBREW:
                return "לא ניתן היה לשלוח את שאלתך. מנהלי מערכת כבר קיבלו הודעה"
            case UserLanguageValues.ENGLISH | _:
                return "Your question could not be submitted. Administrators have already been notified"

    @staticmethod
    def get_question_sent(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Ваш вопрос отправлен, ожидайте ответа от администратора магазина в этом чате"
            case UserLanguageValues.HEBREW:
                return "שאלתך נשלחה, צפה לתגובה ממנהל החנות בצ 'אט זה"
            case UserLanguageValues.ENGLISH | _:
                return "Your question has been sent, expect a response from the store administrator in this chat"

    @staticmethod
    def get_question_sent_cancel(lang: UserLanguageValues) -> str:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return "Отправка вопроса администратору отменена"
            case UserLanguageValues.HEBREW:
                return "שליחת שאלה למנהל בוטלה"
            case UserLanguageValues.ENGLISH | _:
                return "Sending a question to the administrator has been canceled"

    @staticmethod
    def get_back_to_menu_text(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Возвращаюсь в главное меню...")
            case UserLanguageValues.HEBREW:
                return Text("אני חוזר לתפריט הראשי...")
            case UserLanguageValues.ENGLISH | _:
                return Text("Returning to main menu...")

    @staticmethod
    def get_response_text(lang: UserLanguageValues, order_id: str, text: str) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Поступил ответ на вопрос по заказу ", Bold(f"#{order_id} 👇\n\n"), Italic(f"{text}"))
            case UserLanguageValues.HEBREW:
                return Text(" הגיעה תשובה לשאלה בהזמנה ", Bold(f"#{order_id} 👇\n\n"), Italic(f"{text}"))
            case UserLanguageValues.ENGLISH | _:
                return Text(
                    "The answer to the order question has been received ",
                    Bold(f"#{order_id} 👇\n\n"),
                    Italic(f"{text}"),
                )

    @staticmethod
    def get_new_order_status_text(lang: UserLanguageValues, order_id: str, status: str) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Новый статус заказа ", Bold(f"#{order_id}"), "\n", Bold(f"{status}"))
            case UserLanguageValues.HEBREW:
                return Text(" מצב הזמנה חדש ", Bold(f"#{order_id}"), "\n", Bold(f"{status}"))
            case UserLanguageValues.ENGLISH | _:
                return Text("New order status ", Bold(f"#{order_id}"), "\n", Bold(f"{status}"))

    @staticmethod
    def get_yuo_can_add_review_text(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text("Вы можете оставить отзыв ❤️")
            case UserLanguageValues.RUSSIAN:
                return Text("אתה יכול להשאיר משוב ❤️")
            case UserLanguageValues.ENGLISH | _:
                return Text("You can leave a review to your order ❤️")

    @staticmethod
    def get_wait_for_question_message(lang: UserLanguageValues) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(
                    "\n\nПосле отправки вопроса, Вы сможете отправить следующий ",
                    Bold("минимум через 1 час"),
                    " или ",
                    Bold("после ответа администратора"),
                )
            case UserLanguageValues.HEBREW:
                return Text(
                    "\n\nלאחר שליחת השאלה, תוכל לשלוח את הבא ",
                    Bold("תוך שעה לפחות"),
                    " או ",
                    Bold("לאחר תגובת מנהל המערכת"),
                )
            case UserLanguageValues.ENGLISH | _:
                return Text(
                    "\n\nafter sending the question, you will be able to send the following ",
                    Bold("at least 1 hour later"),
                    " or ",
                    Bold("after the administrator's response"),
                )

    @staticmethod
    def get_order_question_confirm_text(lang: UserLanguageValues, order_id: str) -> Text:
        match lang:
            case UserLanguageValues.RUSSIAN:
                return Text(
                    "Вы уверены что хотите отправить это сообщение вопросом к заказу ", Bold(f"#{order_id}"), "?"
                )
            case UserLanguageValues.HEBREW:
                return Text(" אתה בטוח שאתה רוצה לשלוח הודעה זו להזמנה ", Bold(f"#{order_id}"), "?")
            case UserLanguageValues.ENGLISH | _:
                return Text(
                    "Are you sure you want to send this message with question to order ", Bold(f"#{order_id}"), "?"
                )

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
