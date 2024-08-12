from typing import List
from datetime import datetime
from enum import Enum
from aiogram.utils.formatting import Text, Bold

from database.models.product_model import ProductSchema
from database.models.order_option_model import OrderOptionSchema
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
📌 <b>Подробная инструкция:</b> https://ezshoptg.tilda.ws/
"""
    PROVIDER_TOKEN_INSTRUCTION_MESSAGE = """
Чтобы подключить оплату через телеграм в Вашем боте, необходимо получить у @BotFather <b>Provider Token</b> платежной системы и отправить его в чат.

<b>Пошаговая инструкция:</b>

🤖 Откройте чат с @BotFather и введите команду /mybots.

Далее выберите своего бота в списке.

💳 Потом Нажмите кнопку Payments как на 1 фото.

Выберите в списке (фото 2) необходимую Вам платежную систему.

⚙️ Выберите какой вариант оплаты Вам нужен (фото 3) (TEST - тестовая, LIVE - рабочая)

После Вас перекинет в бота платежной системы и после выполнения инструкций от платежного провайдера у Вас в @BotFather, в том же разделе Payments, появится токен для оплаты.

Формат ожидаемого токена: 
Для тестовой оплаты:
<code>1149974399:TEST:3b592a9aaa1b54e58daa</code>
Для рабочей оплаты:
<code>1149974399:LIVE:3b592a9aaa1b54e58daa</code>


📌 Наш канал: @EzShopOfficial
📌 По всем вопросам: @maxzim398
📌 <b>Подробная инструкция:</b> https://ezshoptg.tilda.ws/
    """  # noqa

    SUBSCRIPTION_EXPIRE_NOTIFY = """
Напоминаю о том, что Ваша подписка заканчивается <b>{expire_date}</b> (через <b>{expire_days}</b> дней).
Если Вы хотите продолжить пользоваться ботом, то не забудьте продлить подписку.
С помощью кнопок ниже или в меню команды /check_subscription"""

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

    PAYMENT_METHOD_SETTINGS = "💳 Настройка оплаты для бота @{}:"

    CURRENCY_SELECT_TEXT = "💱 Выберите валюту своего магазина для бота @{}:"

    PAYMENT_SETUP = ("⚙️ Настройка встроенной оплаты для бота @{}"
                     "\n\n⚠️ <b>Обязательно проверьте</b> свой платеж!\nКнопкой «📩 Отправить в Вашего бота»")

    SEND_PAYMENT_SHOW_TO_CUSTOM_BOT = "👀 Показываю как будет выглядеть платёж в Вашем боте."

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

    BOT_CHANNEL_CONTEST_MENU_WHILE_RUNNING = "Сейчас в очереди конкурс в канал <b>@{}</b>\n\n"

    GOODS_COUNT_MESSAGE = (
        "Вы перешли в состояние обновления кол-ва товаров на складе, все отправленные .xlsx файлы "
        "в этом состоянии обновят кол-во товаров.\n\n⬆️Выше отправлена таблица с актуальным списком"
        " товаров и их кол-вом на складе.")

    STOCK_IMPORT_COMMANDS = (
        "1.<b>Перезаписать всё новым содержимым</b>\n"
        "2.<b>При совпадении артикулов - перезаписать</b>\n"
        "3.<b>При совпадении артикулов - оставить старое</b>\n")

    STOCK_IMPORT_FILE_TYPE = (
        "Выберите <b>тип файла</b>, который хотите импортировать: "
    )

    IMPORT_SAMPLE_EXAMPLE = "Загрузите файл с таким шаблоном"

    CONFIRM_STOCK_IMPORT = "Подтвердите импорт:"

    SELECT_CONTEST_TYPE = "Выберите тип конкурса:"

    @staticmethod
    def bot_post_message_menu_message(
            post_message_type: PostMessageType) -> str:
        match post_message_type:
            case PostMessageType.MAILING:
                return "⚙️ Управление текущей рассылки 📨 для бота <b>@{}</b>\n\n" \
                       "❗️Перед запуcком нажмите <b>Проверить</b>, чтобы убедиться в правильности составленного " \
                       "сообщения"
            case PostMessageType.CONTEST:
                return "⚙️ Управление конкурсом 🎲 для канала <b>@{}</b>\n\n" \
                       "❗️Перед запуcком нажмите <b>Проверить</b>, чтобы убедиться в правильности составленного " \
                       "сообщения"
            case PostMessageType.CHANNEL_POST:
                return "⚙️ Управление записью 📋 для канала <b>@{}</b>\n\n" \
                       "❗️Перед запуcком нажмите <b>Проверить</b>, " \
                       "чтобы убедиться в правильности составленного сообщения"
            case PostMessageType.PARTNERSHIP_POST:
                return "⚙️ Управление партнерской записью 🤝 для канала <b>@{}</b>\n\n" \
                       "❗️Перед запуcком нажмите <b>Проверить</b>, чтобы убедиться в правильности составленного " \
                       "сообщения"

    @staticmethod
    def bot_post_already_started_message(
            post_message_type: PostMessageType) -> str:
        match post_message_type:
            case PostMessageType.MAILING:
                return "🙅 Рассылка <b>уже запущена</b>"
            case PostMessageType.CHANNEL_POST:
                return "🙅 Запись <b>уже запущена</b>"
            case PostMessageType.CONTEST:
                return "🙅 Конкурс <b>уже запущен</b>"
            case PostMessageType.PARTNERSHIP_POST:
                return "🙅 Партнерский пост <b>уже запущен</b>"

    @staticmethod
    def bot_post_button_already_exists_message(
            post_message_type: PostMessageType) -> str:
        match post_message_type:
            case PostMessageType.MAILING:
                return "🚫 В рассылочном сообщении кнопка уже есть"
            case PostMessageType.CHANNEL_POST | PostMessageType.PARTNERSHIP_POST:
                return "🚫 В записи кнопка уже есть"

    @staticmethod
    def show_mailing_info(
            sent_post_message_amount: int,
            custom_bot_users_len: int) -> str:
        text = f"Сообщений отправлено:\n" \
            f"{sent_post_message_amount}/{custom_bot_users_len} "

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

    @staticmethod
    def generate_post_order_product_info(products: List[ProductSchema]):
        result = Text(f"На складе кончились эти товары\n\n")
        for product in products:
            result += Text(Bold(product.name), " артикул ", Bold(product.article) + "\n")
        return result.as_kwargs()

    @staticmethod
    def generate_order_options_info(order_options: List[OrderOptionSchema]):
        result = Text("Текущие опции при создании заказв \n\n")

        for oo in sorted(order_options, key=lambda x: x.position_index):
            required_status = "*" if oo.required else ""
            result += Text(oo.position_index, ")  ", Text(oo.emoji), " ",
                           Bold(oo.option_name), " ", required_status + "\n")
        result += Text("\nОпции помеченные * являются обязательными")
        return result.as_kwargs()

    @staticmethod
    def generate_order_option_info(order_option: OrderOptionSchema):
        result = Text(
            "Редактирование опции ",
            order_option.emoji, " ",
            Bold(order_option.option_name),
            "\nномер опции ",
            order_option.position_index,
        )
        return result.as_kwargs()

    @staticmethod
    def generate_publish_product(product: ProductSchema):
        result = f"В продаже " \
            f"{product.name}\n\n" \
            "Цена " \
            f"{product.price}\n\n" \
            f"Успейте купить!"
        return result

    @staticmethod
    def generate_trial_message(trial_duration: int):
        result = Text(
            "Пробная подписка активирована на ",
            Bold(trial_duration),
            " дней",
            "\nЧтобы получить бота с магазином, воспользуйтесь инструкцией ниже 👇",
        )
        return result.as_kwargs()
