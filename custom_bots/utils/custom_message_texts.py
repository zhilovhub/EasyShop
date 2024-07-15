from enum import Enum


class CustomMessageTexts(Enum):
    BOT_ADDED_TO_CHANNEL_MESSAGE = "Ваш бот @{} был <b>добавлен</b> в канал @{}\n\n" \
        "⚙ Для настройки взаимодействия с каналами нажмите на кнопку <b>Мои Каналы</b>"

    BOT_REMOVED_FROM_CHANNEL_MESSAGE = "Ваш бот @{} был <b>удалён</b> из канала @{}"

    @staticmethod
    def show_product_review_info(mark: int, review_text: str, product_name: str):
        return f"Новый отзыв на продукт <b>{product_name}</b>\n\n" \
            f"Оценка - {mark}\n\n" \
            f"Отзыв - {review_text}"
