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
        return "\nЭтот бот может помочь тебе создать свой собственный бот-магазин внутри телеграма"
