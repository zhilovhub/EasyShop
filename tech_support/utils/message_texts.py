from enum import Enum
from aiogram.utils.formatting import Text, Bold, Italic, BlockQuote, Underline


class MessageTexts(Enum):
    @staticmethod
    def get_start_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("👋 Welcome"),
                    " to ",
                    Bold(Italic("EzShop")),
                    " support bot",
                    "\n\n👇 Select what you want to do.",
                )
            case "ru" | _:
                return Text(
                    Bold("👋 Добро пожаловать"),
                    " в бота поддержки ",
                    Bold(Italic("EzShop")),
                    "\n\n👇 Выберите, что хотите сделать.",
                )

    @staticmethod
    def get_faq_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(Bold("❓ Frequently Asked Questions"))
            case "ru" | _:
                return Text(Bold("❓ Часто задаваемые вопросы"))

    @staticmethod
    def get_canceled_sending_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("🚫 Sending the message has been canceled"),
                    Italic("\n\nwrite /start command to return to the menu."),
                )
            case "ru" | _:
                return Text(
                    Bold("🚫 Оправка сообщения отменена"), Italic("\n\nНапишите /start, чтобы вернуться в меню.")
                )

    @staticmethod
    def get_sended_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("📨 The message has been sent"),
                )
            case "ru" | _:
                return Text(
                    Bold("📨 Сообщение отправлено"),
                )

    @staticmethod
    def get_response_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("📩 Received a response from the admin"),
                )
            case "ru" | _:
                return Text(
                    Bold("📩 Получен ответ от админа"),
                )

    @staticmethod
    def get_suggest_update_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("📨 Send a message to the bot with a suggestion to update our services"),
                    '"\n\n We will definitely listen to you and try to make our service even better!',
                )
            case "ru" | _:
                return Text(
                    Bold("📨 Отправьте в лс боту сообщение с предложением обновления наших сервисов"),
                    "\n\nМы обязательно прислушаемся к Вам и постараемся сделать наш сервис еще лучше!",
                )

    @staticmethod
    def get_ask_question_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("📨 Send a message to the bot with a question about our services"),
                    '"\n\nWe will try to answer you as soon as possible and we will definitely help you!',
                )
            case "ru" | _:
                return Text(
                    Bold("📨 Отправьте в лс боту сообщение с вопросом о наших сервисах"),
                    "\n\nПостараемся ответить Вам, как можно скорее и обязательно поможем!",
                )

    @staticmethod
    def get_payment_faq_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("💳 How payments work?"),
                    "\n\nYou can select one of payment methods from list below.",
                    Bold("\n\n🤝 Manual payments:"),
                    BlockQuote("Manual payment, for example, to offer a QR code of the SBP or transfer to a card"),
                    Bold("\n\n📱 Payments with telegram:"),
                    BlockQuote(
                        "Payment via official telegram payment services, "
                        "for example, you can connect Stripe "
                        "(a list of all payments can be viewed in @BotFather)"
                    ),
                    Bold("\n\n⭐️ Payments with telegram stars:"),
                    BlockQuote("Payment via Telegram stars (suitable only for digital goods)."),
                    Italic(
                        "\n\nIf you still have questions, you can ask a question, enter the command /start and "
                        'click on the "ask a question" button'
                    ),
                )
            case "ru" | _:
                return Text(
                    Bold("💳 Как происходит оплата в боте?"),
                    "\n\nВ нашем боте Вы можете подключить 1 из 3 видов оплаты.",
                    Bold("\n\n🤝 Ручная оплата:"),
                    BlockQuote("Оплата в ручную, например предлагать qr код СБП или перевод на карту."),
                    Bold("\n\n📱 Оплата через телеграм:"),
                    BlockQuote(
                        "Оплата через официальные телеграммные платежные сервисы, "
                        "например можно подключить сберкассу "
                        "(список всех платежек можно посмотреть в @BotFather)"
                    ),
                    Bold("\n\n⭐️ Оплата в звездах:"),
                    BlockQuote("Оплата через телеграм звезды (подходит только для цифровых товаров)."),
                    Italic(
                        "\n\nЕсли у Вас остались вопросы то вы можете задать вопрос, введите команду /start и "
                        'нажмите на кнопку "задать вопрос"'
                    ),
                )

    @staticmethod
    def get_admins_faq_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("👥 Is it possible to add multiple admins to the store?"),
                    "\n\nIn our bot, you ",
                    Underline(Bold("can")),
                    " connect several admins.",
                    "\n\nAdmins in the bot will have all the same rights as you, ",
                    " except the rights to delete the bot and manage other admins.",
                    Italic(
                        "\n\nIf you still have questions, you can ask a question, enter the command /start and "
                        'click on the "ask a question" button'
                    ),
                )
            case "ru" | _:
                return Text(
                    Bold("👥 Можно ли добавить несколько админов в магазин?"),
                    "\n\nВ нашем боте Вы ",
                    Underline(Bold("можете")),
                    " подключить несколько админов.",
                    "\n\nАдмины в боте будут иметь все те же права, что и Вы, ",
                    "кроме прав на удаление бота и управления другими админами.",
                    Italic(
                        "\n\nЕсли у Вас остались вопросы то вы можете задать вопрос, введите команду /start и "
                        'нажмите на кнопку "задать вопрос"'
                    ),
                )

    @staticmethod
    def get_customization_faq_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("What can be customized in the bot?"),
                    "\n\n In our bot, you can configure parameters such as:",
                    Bold("\n\n📱 Application design:"),
                    BlockQuote(
                        "You can customize all the colors of the store manually, "
                        " or choose one of the themes we created."
                    ),
                    Bold("\n\n📦 Product options:"),
                    BlockQuote("You can customize various options for products, " " or create your own."),
                    Bold("\n\n🚛 Order setting:"),
                    BlockQuote(
                        "You can customize how the order will be made, for example, enable auto-reduction of "
                        "goods in stock or give the opportunity to choose a delivery method"
                    ),
                    Italic(
                        "\n\nIf you still have questions, you can ask a question, enter the command /start and "
                        'click on the "ask a question" button'
                    ),
                )
            case "ru" | _:
                return Text(
                    Bold("🎨 Что можно кастомизировать в боте?"),
                    "\n\nВ нашем боте Вы можете настраивать такие параметры как:",
                    Bold("\n\n📱 Дизайн приложения:"),
                    BlockQuote(
                        "Вы сможете настроить все цвета магазина вручную, " "или выбрать одну из созданных нами тем."
                    ),
                    Bold("\n\n📦 Опции товаров:"),
                    BlockQuote("Вы сможете настроить различные опции для товаров, " "или создать собственные."),
                    Bold("\n\n🚛 Настройка заказ:"),
                    BlockQuote(
                        "Вы сможете настроить то как будет происходить заказ, например включить автоуменьшение "
                        "товаров на складе или дать возможность выбрать способ доставки"
                    ),
                    Italic(
                        "\n\nЕсли у Вас остались вопросы то вы можете задать вопрос, введите команду /start и "
                        'нажмите на кнопку "задать вопрос"'
                    ),
                )

    @staticmethod
    def get_restrictions_faq_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("🚫 What are the limitations in our bot?"),
                    '"\n\n In our bot You ',
                    Underline(Bold("can")),
                    " create ",
                    Underline(Bold("unlimited")),
                    " number of products.",
                    "\n\nreceive as many orders as you want and have as many customers.\n\n",
                    BlockQuote(
                        "We constantly monitor the load on our servers and, "
                        "if necessary, promptly increase capacity."
                    ),
                    Italic(
                        "\n\nIf you still have questions, you can ask a question, enter the command /start and "
                        'click on the "ask a question" button'
                    ),
                )
            case "ru" | _:
                return Text(
                    Bold("🚫 Какие ограничения есть в нашем боте?"),
                    "\n\nВ нашем боте Вы ",
                    Underline(Bold("можете")),
                    " создать ",
                    Underline(Bold("неограниченное")),
                    " количество товаров.",
                    "\n\nПолучать сколько угодно заказов и иметь столько же клиентов.\n\n",
                    BlockQuote(
                        "Мы постоянно следим за нагрузкой на наши "
                        "сервера и в случае необходимости оперативно увеличиваем мощность."
                    ),
                    Italic(
                        "\n\nЕсли у Вас остались вопросы то вы можете задать вопрос, введите команду /start и "
                        'нажмите на кнопку "задать вопрос"'
                    ),
                )

    @staticmethod
    def get_export_faq_message_text(lang: str) -> Text:
        # TODO replace lang to lang enum from db (translate_shop branch)
        match lang:
            case "eng":
                return Text(
                    Bold("🔽 Is it possible to export / import goods in a bot?"),
                    '"\n\n In our bot you are ',
                    Underline(Bold("can")),
                    " export or import tables with a list of products.\n\n",
                    BlockQuote('You can do this in the "My products" section in the bot settings menu.'),
                    Italic(
                        "\n\nIf you still have questions, you can ask a question, enter the command /start and "
                        'click on the "ask a question" button'
                    ),
                )
            case "ru" | _:
                return Text(
                    Bold("🔽 Возможно ли экспортировать / импортировать товары в боте?"),
                    "\n\nВ нашем боте Вы ",
                    Underline(Bold("можете")),
                    " экспортировать или импортировать таблицы со списком товаров.\n\n",
                    BlockQuote('Сделать это можно в разделе "Мои товары" в меню настроек бота.'),
                    Italic(
                        "\n\nЕсли у Вас остались вопросы то вы можете задать вопрос, введите команду /start и "
                        'нажмите на кнопку "задать вопрос"'
                    ),
                )
