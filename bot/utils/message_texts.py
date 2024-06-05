from enum import Enum


class MessageTexts(Enum):
    ABOUT_MESSAGE = "Приветствую! Спасибо, что решили воспользоваться нашими услугами 🔥"

    INSTRUCTION_MESSAGE = """<b>Чтобы</b>

🔥 Создать бота, 
🔥 Проинициализировать в нем веб приложение магазина 
🔥 Получить панель управления

Вам <b>всего лишь</b> нужно отправить <b>нам в чат</b> одно сообщение - <b>токен</b> бота, которого и будут использовать Ваши покупатели


❗ <b>Токены для ботов</b> выдает отец всех ботов - <b>официальный бот Телеграмма @BotFather</b>
Напишите ему <b>три сообщения</b> и получите свой токен

Там все легко, но вот <b>видео</b> на всякий случай 📷

📌 Подписаться на канал: @EzShopOfficial
"""

    FREE_TRIAL_MESSAGE = """
Вам назначен <b>пробный период</b> пользованием нашего бота со <b>всем</b> функционалом <b>бесплатно</b>, 1<b> неделя.</b>
Нажмите на кнопку ниже, и пробный период начнется. 
Вам не нужно нам кидать никакие данные от карт, просто нажимайте на кнопку и получайте профит"""

    SUBSCRIPTION_EXPIRE_NOTIFY = """
Напоминаю о том, что Ваша подписка заканчивается <b>{expire_date}</b> (через <b>{expire_days}</b> дней).
Если Вы хотите продолжить пользоваться ботом, то не забудьте продлить подписку.
С помощью кнопок ниже или в меню команды /check_subscription
"""

    SUBSCRIBE_END_NOTIFY = """
Ваша подписка <b>закончилась</b> :(
Ваши боты <b>приостановлены</b>.
Продлить подписку можно по кнопке ниже, если подписка будет неактивна <b>больше месяца</b>, мы <b>удалим все данные</b> о Вашем боте
"""

    BACK_BUTTON_TEXT = "🔙 Назад"

    OPEN_WEB_APP_BUTTON_TEXT = "Открыть магазин"

    BOT_INITIALIZING_MESSAGE = "Ваш бот с именем <b>«{}»</b>\nи id <b>@{}</b> найден!\n\n" \
                               "Веб магазин в нем проиницализируется в течение <b>5 минут</b>"

    BOT_WITH_TOKEN_NOT_FOUND_MESSAGE = "Бота с таким токеном не сущесвует. " \
                                       "Скопируйте токен, который Вам выслал <b>@BotFather</b>"

    INCORRECT_BOT_TOKEN_MESSAGE = "Неверный формат токена. " \
                                  "Он должен иметь вид:\n<code>3742584906:AAHAE1daXFuQJrmSITDrgmbP0c8C3JmQNeg</code>"

    DEFAULT_START_MESSAGE = "Здравствуйте, <b>{name}</b>! Для открытия магазина нажмите на кнопку магазин"

    BOT_MENU_MESSAGE = "Меню бота @{}:"

    BOT_CHANNELS_LIST_MESSAGE = "Список <b>каналов</b>, принадлежащих боту @{}: "

    BOT_CHANNEL_MENU_MESSAGE = "Администрирование <b>канала</b> @{} <b>ботом</b> @{}"

    BOT_COMPETITIONS_LIST_MESSAGE = "Список <b>конкурсов</b>, принадлежащих боту @{}: "

    BOT_COMPETITION_MENU_MESSAGE = "Настройки конкурса {}\n" \
                                   "Канал: @{}\n" \
                                   "Бот: @{}"

    BOT_ADDED_TO_CHANNEL_MESSAGE = "Ваш бот @{} был <b>добавлен</b> в канал @{}\n\n" \
        "⚙ Для настройки взаимодействия с каналами нажмите на кнопку <b>Мои Каналы</b>"

    BOT_REMOVED_FROM_CHANNEL_MESSAGE = "Ваш бот @{} был <b>удалён</b> из канала @{}"

    BOT_MAILINGS_MENU_MESSAGE = "Управление текущей рассылки для бота <b>@{}</b>\n\n" \
        "❗️Перед запуcком нажмите <b>Проверить</b>, чтобы убедиться в правильности составленного сообщения"

    BOT_MAILINGS_MENU_ACCEPT_START = "Управление текущей рассылки для бота <b>@{}</b>\n\n" \
                                     "<b>Подтверждение начала рассылки</b>"

    BOT_MAILINGS_MENU_ACCEPT_DELETING_MESSAGE = "Управление текущей рассылки для бота <b>@{}</b>\n\n" \
                                                "<b>Подтверждение удаления рассылки</b>"

    BOT_MAILING_MENU_WHILE_RUNNING = "Сейчас идет рассылка для бота <b>@{}</b>\n\n"

    CONTACTS = f"Генеральный директор:\n" \
               f"Тг: <b>@maxzim398</b>\n\n" \
               f"Технический директор:\n" \
               f"Тг: <b>@Ilyyasha</b>"

    DATE_RULES = "Пожалуйста, отправьте дату и время в следующем формате: ДД.ММ.ГГГГ ЧЧ:ММ\n" \
        "Например, 25.12.2024 14:30"
