from .default import DefaultLocale


class EnglishLocale(DefaultLocale):

    @property
    def start_message(self) -> str:
        return "Hello <b>{name}</b>!" \
               "\n\nFor start, select the language (выбери язык)."

    @property
    def locale_set(self):
        return "Language set to 🇬🇧 \"English\""

    @property
    def about_message(self) -> str:
        return "\nThis bot can help you with creation of your own bot-shop inside telegram app."
