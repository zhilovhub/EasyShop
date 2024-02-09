class DefaultLocale:

    @property
    def start_message(self):
        return "Привет <b>{name}</b>!" \
               "\n\nДля начала выбери язык (select language)."

    @property
    def locale_set(self):
        return "Язык установлен на 🇷🇺 \"Русский\""

    @property
    def about_message(self) -> str:
        return "\nЭтот бот может помочь тебе создать свой собственный бот-магазин внутри телеграма." \
               "\n\nВыбери, что хочешь сделать:"

    @property
    def main_menu_buttons(self) -> dict:
        return {'add': "➕ Создать бота", 'bots': "📋 Мои боты", 'profile':  "👤 Мой профиль"}

    @property
    def input_token(self) -> str:
        return ("Введи токен из <b>@BotFather</b> в формате:\n\n"
                "<code>0000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA</code>")

    @property
    def back_to_menu_button(self) -> str:
        return "🔙 Назад"

    @property
    def open_web_app_button(self) -> str:
        return "Открыть магазин"

    @property
    def bot_will_initialize(self) -> str:
        return ("Твой бот с именем <b>«{}»</b>\nи id <b>@{}</b> найден!\n\nВеб магазин в нем "
                "проиницализируется в течение <b>5 минут</b>")

    @property
    def bot_with_token_not_found(self) -> str:
        return "Бота с таким токеном не сущесвует. Скопируй токен, который тебе выслал <b>@BotFather</b>"

    @property
    def incorrect_bot_token(self) -> str:
        return ("Неверный формат токена. "
                "Он должен иметь вид:\n<code>0000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA</code>"
                "\n\nПример:\n<code>3742584906:AAHAE1daXFuQJrmSITDrgmbP0c8C3JmQNeg</code>")

    @property
    def default_start_msg(self) -> str:
        return "Привет, <b>{name}</b>! Для открытия магазина нажми на кнопку ниже или на опцию в меню."

    @property
    def you_dont_have_bots_msg(self) -> str:
        return "У тебя еще нет ботов."

    @property
    def my_bots_msg(self) -> str:
        return "Выбери бота из списка:"

    @property
    def bot_not_found_msg(self) -> str:
        return "Выбранный бот не найден в базе, попробуйте обновить список ботов."

    @property
    def selected_bot_buttons(self) -> dict:
        return {'start_msg': "👋 Стартовое сообщение", 'shop_btn': "🔤 Текст кнопки открытия магазина"}

    @property
    def selected_bot_msg(self) -> str:
        return "Выбран бот <b>{selected_name}</b>, выбери настройку, которую хочешь сменить."
