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

    @property
    def default_start_msg(self) -> str:
        return "Hi, <b>{name}</b>! To open shop you can press button bellow or button in attachments menu."

    @property
    def you_dont_have_bots_msg(self) -> str:
        return "You dont have bots yet."

    @property
    def my_bots_msg(self) -> str:
        return "Choose bot from list:"

    @property
    def bot_not_found_msg(self) -> str:
        return "Selected bot not found in database, try updating bots list."

    @property
    def selected_bot_buttons(self) -> dict:
        return {'start_msg': "👋 Hello message", 'shop_btn': "🔤 Open shop button text"}

    @property
    def selected_bot_msg(self) -> str:
        return "Selected bot: <b>{selected_name}</b>\nChoose option that you want to set up."
