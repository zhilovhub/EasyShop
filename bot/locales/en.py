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
        return "\nThis bot can help you with creation of your own bot-shop inside telegram app." \
               "\n\nSelect the option from list bellow:"

    @property
    def main_menu_buttons(self) -> dict:
        return {'add': "➕ Create bot", 'bots': "📋 My bots", 'profile':  "👤 My profile"}

    @property
    def input_token(self) -> str:
        return ("Enter API TOKEN from <b>@BotFather</b> in format:\n\n"
                "<code>0000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA</code>")

    @property
    def back_to_menu_button(self) -> str:
        return "🔙 Back"

    @property
    def open_web_app_button(self) -> str:
        return "Open shop"
