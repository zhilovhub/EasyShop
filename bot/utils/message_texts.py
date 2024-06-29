from enum import Enum

from bot.enums.post_message_type import PostMessageType


class MessageTexts(Enum):
    INSTRUCTION_MESSAGE = """<b>Чтобы</b>

🔥 Создать бота, 
🔥 Проинициализировать в нем веб приложение магазина 
🔥 Получить панель управления

Вам <b>всего лишь</b> нужно отправить <b>нам в чат</b> одно сообщение - <b>токен</b> бота, которого и будут использовать Ваши покупатели


❗ <b>Токены для ботов</b> выдает отец всех ботов - <b>официальный бот Телеграмма @BotFather</b>
Напишите ему <b>три сообщения</b> и получите свой токен

Там все легко, но вот <b>видео</b> на всякий случай 📷

📌 Подписаться на канал: @EzShopOfficial
"""  # noqa

    FREE_TRIAL_MESSAGE = "Здравствуйте! У Вас активирована пробная подписка на <b>1 неделю</b>\n" \
                         "Чтобы получить бота с магазином, воспользуйтесь инструкцией ниже 👇"

    SUBSCRIPTION_EXPIRE_NOTIFY = """
Напоминаю о том, что Ваша подписка заканчивается <b>{expire_date}</b> (через <b>{expire_days}</b> дней).
Если Вы хотите продолжить пользоваться ботом, то не забудьте продлить подписку.
С помощью кнопок ниже или в меню команды /check_subscription
"""

    SUBSCRIBE_END_NOTIFY = """
Ваша подписка <b>закончилась</b> :(
Ваши боты <b>приостановлены</b>.
Продлить подписку можно по кнопке ниже, если подписка будет неактивна <b>больше месяца</b>, мы <b>удалим все данные</b> о Вашем боте
"""  # noqa

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

    BOT_ADDED_TO_CHANNEL_MESSAGE = "Ваш бот @{} был <b>добавлен</b> в канал @{}\n\n" \
        "⚙ Для настройки взаимодействия с каналами нажмите на кнопку <b>Мои Каналы</b>"

    BOT_REMOVED_FROM_CHANNEL_MESSAGE = "Ваш бот @{} был <b>удалён</b> из канала @{}"

    BOT_MAILINGS_MENU_ACCEPT_START = "Управление текущей рассылки для бота <b>@{}</b>\n\n" \
                                     "<b>Подтверждение начала рассылки</b>"

    BOT_MAILINGS_MENU_ACCEPT_DELETING_MESSAGE = "Управление текущей рассылки для бота <b>@{}</b>\n\n" \
                                                "<b>Подтверждение удаления рассылки</b>"

    BOT_MAILING_MENU_WHILE_RUNNING = "Сейчас идет рассылка для бота <b>@{}</b>\n\n"

    CONTACTS = f"Генеральный директор:\n" \
               f"Тг: <b>@maxzim398</b>\n\n" \
               f"Технический директор:\n" \
               f"Тг: <b>@Ilyyasha</b>"

    DATE_RULES = "Пожалуйста, отправьте дату и время <b>начала отправки сообщения</b> в следующем формате: " \
                 "<b>ДД.ММ.ГГГГ ЧЧ:ММ</b>\nНапример, <code>25.12.2024 14:30</code>"

    BOT_CHANNEL_POST_MENU_ACCEPT_START = "Управление записью для канала <b>@{}</b>\n\n" \
        "<b>Подтверждение начала рассылки</b>"

    BOT_CHANNEL_POST_MENU_ACCEPT_DELETING_MESSAGE = "Управление записью для канала <b>@{}</b>\n\n" \
        "<b>Подтверждение удаления рассылки</b>"

    BOT_CHANNEL_POST_MENU_WHILE_RUNNING = "Сейчас в очереди пост в канал <b>@{}</b>\n\n"

    GOODS_COUNT_MESSAGE = ("Вы перешли в состояние обновления кол-ва товаров на складе, все отправленные .xlsx файлы "
                           "в этом состоянии обновят кол-во товаров.\n\n⬇️ Ниже отправлена таблица с актуальным списком"
                           " товаров и их кол-вом на складе.")

    STOCK_IMPORT_COMMANDS = ("1.<b>Перезаписать всё новым содержимым</b>\n"
                             "2.<b>При совпадении артикулов - перезаписать</b>\n"
                             "3.<b>При совпадении артикулов - оставить старое</b>\n")

    @staticmethod
    def bot_post_message_menu_message(post_message_type: PostMessageType) -> str:
        match post_message_type:
            case PostMessageType.MAILING:
                return "Управление текущей рассылки для бота <b>@{}</b>\n\n" \
                       "❗️Перед запуcком нажмите <b>Проверить</b>, чтобы убедиться в правильности составленного " \
                       "сообщения"
            case PostMessageType.CHANNEL_POST:
                return "Управление записью для канала <b>@{}</b>\n\n" \
                       "❗️Перед запуcком нажмите <b>Проверить</b>, " \
                       "чтобы убедиться в правильности составленного сообщения"

    @staticmethod
    def bot_post_already_done_message(post_message_type: PostMessageType) -> str:
        match post_message_type:
            case PostMessageType.MAILING:
                return "Рассылка уже завершена или удалена"
            case PostMessageType.CHANNEL_POST:
                return "Запись уже выложена или удалена"

    @staticmethod
    def bot_post_already_started_message(post_message_type: PostMessageType) -> str:
        match post_message_type:
            case PostMessageType.MAILING:
                return "Рассылка уже запущена"
            case PostMessageType.CHANNEL_POST:
                return "Запись уже запущена"

    @staticmethod
    def bot_post_button_already_exists_message(post_message_type: PostMessageType) -> str:
        match post_message_type:
            case PostMessageType.MAILING:
                return "В рассылочном сообщении кнопка уже есть"
            case PostMessageType.CHANNEL_POST:
                return "В записи кнопка уже есть"
