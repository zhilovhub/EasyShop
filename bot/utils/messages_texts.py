class DefaultLocale:
    @staticmethod
    def about_message() -> str:
        return "Этот бот может помочь тебе создать свой собственный\nбот-магазин внутри телеграма."

    @staticmethod
    def main_menu_buttons() -> dict:
        return {'add': "➕ Создать бота", 'bots': "📋 Мои боты", 'profile':  "👤 Мой профиль"}

    @staticmethod
    def input_token() -> str:
        return ("Чтобы создать бота, введи токен, который ты можешь достать у <b>@BotFather</b> в формате:\n\n"
                "<code>3742584906:AAHAE1daXFuQJrmSITDrgmbP0c8C3JmQNeg</code>")

    @staticmethod
    def back_button() -> str:
        return "🔙 Назад"

    @staticmethod
    def open_web_app_button() -> str:
        return "Открыть магазин"

    @staticmethod
    def bot_will_initialize() -> str:
        return ("Твой бот с именем <b>«{}»</b>\nи id <b>@{}</b> найден!\n\nВеб магазин в нем "
                "проиницализируется в течение <b>5 минут</b>")

    @staticmethod
    def bot_with_token_not_found() -> str:
        return "Бота с таким токеном не сущесвует. Скопируй токен, который тебе выслал <b>@BotFather</b>"

    @staticmethod
    def incorrect_bot_token() -> str:
        return ("Неверный формат токена. "
                "Он должен иметь вид:\n<code>3742584906:AAHAE1daXFuQJrmSITDrgmbP0c8C3JmQNeg</code>")

    @staticmethod
    def default_start_msg() -> str:
        return "Привет, <b>{name}</b>! Для открытия магазина нажми на кнопку магазин."

    @staticmethod
    def you_dont_have_bots_msg() -> str:
        return "У тебя еще нет ботов."

    @staticmethod
    def my_bots_msg() -> str:
        return "Выбери бота из списка:"

    @staticmethod
    def bot_not_found_msg() -> str:
        return "Выбранный бот не найден в базе, попробуйте обновить список ботов."

    @staticmethod
    def selected_bot_buttons() -> dict:
        return {'start_msg': "👋 Стартовое сообщение", 'shop_btn': "🔤 Текст кнопки открытия магазина",
                "add_products": "🛍 Добавить товары"}

    @staticmethod
    def selected_bot_msg() -> str:
        return "Выбран бот <b>{selected_name}</b>, выбери настройку, которую хочешь сменить."
