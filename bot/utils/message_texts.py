from datetime import datetime
from enum import Enum

from database.models.post_message_model import PostMessageType


class MessageTexts(Enum):
    INSTRUCTION_MESSAGE = """
Чтобы воспользоваться нашим сервисом, введите <b>токен</b> бота, который Вы можете получить у @BotFather.

<b>Для чего?</b>

🛍 Именно к этому боту прикрепится <b>магазин</b>

⚙️ Именно этого бота Вы сможете <b>настраивать</b>

🧍 Именно через него к Вам будут поступать <b>клиенты</b>


Формат ожидаемого токена: <code>3742584906:AAHAE1daXFuQJrmSITDrgmbP0c8C3JmQNeg</code>


📌 Наш канал: @EzShopOfficial
📌 По всем вопросам: @maxzim398
"""

    FREE_TRIAL_MESSAGE = "Здравствуйте! У Вас активирована пробная подписка на <b>3 дня</b>\n" \
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

    BOT_MAILINGS_MENU_ACCEPT_START = "Управление текущей рассылки для бота <b>@{}</b>\n\n" \
                                     "<b>Подтверждение начала рассылки</b>"

    BOT_MAILINGS_MENU_ACCEPT_DELETING_MESSAGE = "Управление текущей рассылки для бота <b>@{}</b>\n\n" \
                                                "<b>Подтверждение удаления рассылки</b>"

    BOT_MAILING_MENU_WHILE_RUNNING = "Сейчас идет рассылка для бота <b>@{}</b>\n\n"

    CONTACTS = f"Генеральный директор:\n" \
        f"Тг: <b>@maxzim398</b>\n\n" \
        f"Технический директор:\n" \
        f"Тг: <b>@Ilyyasha</b>"

    BOT_CHANNEL_POST_MENU_ACCEPT_START = "Управление записью для канала <b>@{}</b>\n\n" \
        "<b>Подтверждение начала отправления записи в канал</b>"

    BOT_CHANNEL_POST_MENU_ACCEPT_DELETING_MESSAGE = "Управление записью для канала <b>@{}</b>\n\n" \
        "<b>Подтверждение удаления редактируемого сообщения</b>"

    BOT_CHANNEL_POST_MENU_WHILE_RUNNING = "Сейчас в очереди запись в канал <b>@{}</b>\n\n"

    GOODS_COUNT_MESSAGE = (
        "Вы перешли в состояние обновления кол-ва товаров на складе, все отправленные .xlsx файлы "
        "в этом состоянии обновят кол-во товаров.\n\n⬇️ Ниже отправлена таблица с актуальным списком"
        " товаров и их кол-вом на складе.")

    STOCK_IMPORT_COMMANDS = (
        "1.<b>Перезаписать всё новым содержимым</b>\n"
        "2.<b>При совпадении артикулов - перезаписать</b>\n"
        "3.<b>При совпадении артикулов - оставить старое</b>\n")

    SELECT_CONTEST_TYPE = "Выберите тип конкурса:"

    @staticmethod
    def bot_post_message_menu_message(
            post_message_type: PostMessageType) -> str:
        match post_message_type:
            case PostMessageType.MAILING:
                return "Управление текущей рассылки для бота <b>@{}</b>\n\n" \
                       "❗️Перед запуcком нажмите <b>Проверить</b>, чтобы убедиться в правильности составленного " \
                       "сообщения"
            case PostMessageType.CONTEST:
                return "Управление конкурсом для канала <b>@{}</b>\n\n" \
                       "❗️Перед запуcком нажмите <b>Проверить</b>, чтобы убедиться в правильности составленного " \
                       "сообщения"
            case PostMessageType.CHANNEL_POST:
                return "Управление записью для канала <b>@{}</b>\n\n" \
                       "❗️Перед запуcком нажмите <b>Проверить</b>, " \
                       "чтобы убедиться в правильности составленного сообщения"

    @staticmethod
    def bot_post_already_started_message(
            post_message_type: PostMessageType) -> str:
        match post_message_type:
            case PostMessageType.MAILING:
                return "Рассылка уже запущена"
            case PostMessageType.CHANNEL_POST:
                return "Запись уже запущена"

    @staticmethod
    def bot_post_button_already_exists_message(
            post_message_type: PostMessageType) -> str:
        match post_message_type:
            case PostMessageType.MAILING:
                return "В рассылочном сообщении кнопка уже есть"
            case PostMessageType.CHANNEL_POST:
                return "В записи кнопка уже есть"

    @staticmethod
    def show_mailing_info(
            sent_post_message_amount: int,
            custom_bot_users_len: int) -> str:
        text = f"Сообщений отправлено:\n" \
            f"<b>{sent_post_message_amount}/{custom_bot_users_len}</b>"

        if sent_post_message_amount != custom_bot_users_len:
            text += f"\n\n❗ Во время рассылки было обнаружено, что бота забанило " \
                f"{custom_bot_users_len - sent_post_message_amount} человек"

        return text

    @staticmethod
    def show_date_rules(name: str):
        date_now = datetime.now().strftime("%d.%m.%Y %H:%M")
        return f"📅 Пожалуйста, отправьте дату и время <b>{name}</b> в следующем формате: " \
            f"\n<b>ДД.ММ.ГГГГ ЧЧ:ММ</b>\n\nНапример: <code>{date_now}</code>" \
            f"\n\n<i>* нажмите на дату в примере ☝️ чтобы её скопировать.</i>"
