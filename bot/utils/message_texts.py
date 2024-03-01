from enum import Enum


class MessageTexts(Enum):
    ABOUT_MESSAGE = "Привет! Рад, что ты захотел воспользоваться нашими услугами 🔥"

    INSTRUCTION_MESSAGE = """Чтобы создать бота, проинициализировать в нем веб приложение магазина и получить панель управления, тебе всего-лишь нужно отправить 
сюда одно сообщение - <b>токен бота</b>, которого и будут использовать твои покупатели

Чтобы получить токен, тебе всего-лишь надо написать официальному боту Телеграмма <b>@BotFather</b>. Скриншоты
помогут тебе, но там все легко 😉
"""

    BACK_BUTTON_TEXT = "🔙 Назад"

    OPEN_WEB_APP_BUTTON_TEXT = "Открыть магазин"

    BOT_INITIALIZING_MESSAGE = "Твой бот с именем <b>«{}»</b>\nи id <b>@{}</b> найден!\n\n" \
                               "Веб магазин в нем проиницализируется в течение <b>5 минут</b>"

    BOT_WITH_TOKEN_NOT_FOUND_MESSAGE = "Бота с таким токеном не сущесвует. " \
                                       "Скопируй токен, который тебе выслал <b>@BotFather</b>"

    INCORRECT_BOT_TOKEN_MESSAGE = "Неверный формат токена. " \
                                  "Он должен иметь вид:\n<code>3742584906:AAHAE1daXFuQJrmSITDrgmbP0c8C3JmQNeg</code>"

    DEFAULT_START_MESSAGE = "Привет, <b>{name}</b>! Для открытия магазина нажми на кнопку магазин"

    BOT_SELECTED_MESSAGE = "Выбран бот <b>{selected_name}</b>, выбери настройку, которую хочешь сменить"
