import re

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.main import bot, cache_resources_file_id_store
from bot.utils import MessageTexts
from bot.states.states import States
from bot.handlers.routers import custom_bot_editing_router
from bot.utils.send_instructions import send_instructions
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard, ReplyBackBotMenuKeyboard

from common_utils.bot_utils import create_bot_options
from common_utils.config import common_settings
from common_utils.invoice import create_invoice_params
from common_utils.keyboards.keyboards import InlineBotEditOrderOptionKeyboard, InlineBotEditOrderOptionsKeyboard, \
    InlineBotMenuKeyboard, InlineBotSettingsMenuKeyboard, InlineEditOrderChooseOptionKeyboard, \
    InlineEditOrderOptionTypeKeyboard, InlinePaymentSettingsKeyboard, InlineCurrencySelectKeyboard, \
    InlinePaymentSetupKeyboard

from database.config import bot_db, option_db, order_option_db, order_choose_option_db
from database.models.option_model import OptionNotFoundError, CurrencyCodesValues, CurrencySymbolsValues
from database.models.order_option_model import OrderOptionNotFoundError, OrderOptionSchemaWithoutId, \
    OrderOptionTypeValues
from database.models.order_choose_option_model import OrderChooseOptionSchemaWithoutId
from database.models.bot_model import BotPaymentTypeValues

from logs.config import logger


def _is_valid_hex_code(string: str) -> bool:
    """Проверяет, валидный ли цвет передал пользователь"""

    regex = "^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"

    p = re.compile(regex)

    if string is None:
        return False

    if re.search(p, string):
        return True
    else:
        return False


@custom_bot_editing_router.callback_query(
    lambda query: InlinePaymentSettingsKeyboard.callback_validator(query.data)
)
async def manage_payment_settings(query: CallbackQuery, state: FSMContext):
    callback_data = InlinePaymentSettingsKeyboard.Callback.model_validate_json(query.data)

    custom_bot = await bot_db.get_bot(callback_data.bot_id)
    custom_bot_data = await Bot(custom_bot.token).get_me()
    custom_bot_options = await option_db.get_option(custom_bot.options_id)

    # check if currency code is still xtr, but stars is not selected
    if custom_bot.payment_type != BotPaymentTypeValues.STARS and custom_bot_options.currency_code == CurrencyCodesValues.TELEGRAM_STARS:
        custom_bot_options.currency_code = CurrencyCodesValues.RUSSIAN_RUBLE
        custom_bot_options.currency_symbol = CurrencySymbolsValues.RUSSIAN_RUBLE
        await option_db.update_option(custom_bot_options)

    match callback_data.a:
        case callback_data.ActionEnum.MANUAL_METHOD:
            custom_bot.payment_type = BotPaymentTypeValues.MANUAL
            await bot_db.update_bot(custom_bot)
            await query.message.edit_text(
                MessageTexts.PAYMENT_METHOD_SETTINGS.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSettingsKeyboard.get_keyboard(custom_bot.bot_id,
                                                                              custom_bot.payment_type)
            )
            return await query.answer("🤝 Выбран ручной метод оплаты", show_alert=True)
        case callback_data.ActionEnum.TG_PROVIDER:
            custom_bot.payment_type = BotPaymentTypeValues.TG_PROVIDER
            await bot_db.update_bot(custom_bot)
            await query.message.edit_text(
                MessageTexts.PAYMENT_METHOD_SETTINGS.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSettingsKeyboard.get_keyboard(custom_bot.bot_id,
                                                                              custom_bot.payment_type)
            )
            return await query.answer("📱 Выбран метод оплаты через телеграм.\n\n"
                                      "❗️ Не забудьте указать provider token в настройках платежки.",
                                      show_alert=True)
        case callback_data.ActionEnum.STARS:
            custom_bot.payment_type = BotPaymentTypeValues.STARS
            custom_bot_options.currency_code = CurrencyCodesValues.TELEGRAM_STARS
            custom_bot_options.currency_symbol = CurrencySymbolsValues.TELEGRAM_STARS
            await bot_db.update_bot(custom_bot)
            await option_db.update_option(custom_bot_options)
            await query.message.edit_text(
                MessageTexts.PAYMENT_METHOD_SETTINGS.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSettingsKeyboard.get_keyboard(custom_bot.bot_id,
                                                                              custom_bot.payment_type)
            )
            return await query.answer("⭐️ Выбран метод оплаты через телеграм звезды.", show_alert=True)
        case callback_data.ActionEnum.SELECT_CURRENCY:
            if custom_bot.payment_type == BotPaymentTypeValues.STARS:
                return await query.answer("⚠️ При выборе оплаты звездами, нет необходимости указывать валюту.",
                                          show_alert=True)
            return await query.message.edit_text(
                MessageTexts.CURRENCY_SELECT_TEXT.value.format(custom_bot_data.username),
                reply_markup=await InlineCurrencySelectKeyboard.get_keyboard(callback_data.bot_id,
                                                                             custom_bot_options.currency_code)
            )
        case callback_data.ActionEnum.TG_PROVIDER_SETUP | callback_data.ActionEnum.STARS_SETUP:
            if callback_data.a == callback_data.ActionEnum.STARS_SETUP:
                stars = True
            else:
                stars = False
            return await query.message.edit_text(
                MessageTexts.PAYMENT_SETUP.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSetupKeyboard.get_keyboard(custom_bot.bot_id,
                                                                           custom_bot.options_id,
                                                                           stars)
            )
        case callback_data.ActionEnum.BACK_TO_BOT_MENU:
            if custom_bot.payment_type == BotPaymentTypeValues.TG_PROVIDER and not custom_bot.provider_token:
                custom_bot.payment_type = BotPaymentTypeValues.MANUAL
                await bot_db.update_bot(custom_bot)
                await query.answer("⚠️ Вы не указали provider token в настройках платежей."
                                   "\n\nБез этого параметра платежи не будут работать."
                                   "\n\n↩️ Переключаю оплату на ручную.",
                                   show_alert=True)
                return query.message.edit_reply_markup(
                    reply_markup=await InlinePaymentSettingsKeyboard.get_keyboard(custom_bot.bot_id,
                                                                                  custom_bot.payment_type)
                )
            return await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_data.username),
                reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(callback_data.bot_id)
            )


async def _send_provider_token_instructions(user_id: int):
    media = [
        InputMediaPhoto(
            media=FSInputFile(path=common_settings.RESOURCES_PATH.format("provider_token_1.jpg")),
            caption=MessageTexts.PROVIDER_TOKEN_INSTRUCTION_MESSAGE.value,
        ),
        InputMediaPhoto(
            media=FSInputFile(path=common_settings.RESOURCES_PATH.format("provider_token_2.jpg")),
        ),
        InputMediaPhoto(
            media=FSInputFile(path=common_settings.RESOURCES_PATH.format("provider_token_3.jpg")),
        ),
    ]
    await bot.send_media_group(user_id, media)


@custom_bot_editing_router.callback_query(
    lambda query: InlinePaymentSetupKeyboard.callback_validator(query.data)
)
async def manage_payment_settings(query: CallbackQuery, state: FSMContext):
    callback_data = InlinePaymentSetupKeyboard.Callback.model_validate_json(query.data)

    custom_bot = await bot_db.get_bot(callback_data.bot_id)
    custom_bot_tg = Bot(custom_bot.token)
    custom_bot_data = await custom_bot_tg.get_me()
    custom_bot_options = await option_db.get_option(custom_bot.options_id)

    if custom_bot.payment_type == BotPaymentTypeValues.STARS:
        stars = True
    else:
        stars = False

    match callback_data.a:
        case callback_data.ActionEnum.NAME:
            custom_bot_options.request_name_in_payment = not custom_bot_options.request_name_in_payment
            await option_db.update_option(custom_bot_options)
            return await query.message.edit_text(
                MessageTexts.PAYMENT_SETUP.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSetupKeyboard.get_keyboard(custom_bot.bot_id,
                                                                           custom_bot.options_id,
                                                                           stars)
            )
        case callback_data.ActionEnum.EMAIL:
            custom_bot_options.request_email_in_payment = not custom_bot_options.request_email_in_payment
            await option_db.update_option(custom_bot_options)
            return await query.message.edit_text(
                MessageTexts.PAYMENT_SETUP.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSetupKeyboard.get_keyboard(custom_bot.bot_id,
                                                                           custom_bot.options_id,
                                                                           stars)
            )
        case callback_data.ActionEnum.PHONE:
            custom_bot_options.request_phone_in_payment = not custom_bot_options.request_phone_in_payment
            await option_db.update_option(custom_bot_options)
            return await query.message.edit_text(
                MessageTexts.PAYMENT_SETUP.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSetupKeyboard.get_keyboard(custom_bot.bot_id,
                                                                           custom_bot.options_id,
                                                                           stars)
            )
        case callback_data.ActionEnum.SHIPPING:
            custom_bot_options.request_address_in_payment = not custom_bot_options.request_address_in_payment
            await option_db.update_option(custom_bot_options)
            return await query.message.edit_text(
                MessageTexts.PAYMENT_SETUP.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSetupKeyboard.get_keyboard(custom_bot.bot_id,
                                                                           custom_bot.options_id,
                                                                           stars)
            )
        case callback_data.ActionEnum.PHOTO:
            custom_bot_options.show_photo_in_payment = not custom_bot_options.show_photo_in_payment
            await option_db.update_option(custom_bot_options)
            return await query.message.edit_text(
                MessageTexts.PAYMENT_SETUP.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSetupKeyboard.get_keyboard(custom_bot.bot_id,
                                                                           custom_bot.options_id,
                                                                           stars)
            )
        case callback_data.ActionEnum.WEBVIEW:
            custom_bot_options.show_payment_in_webview = not custom_bot_options.show_payment_in_webview
            await option_db.update_option(custom_bot_options)
            return await query.message.edit_text(
                MessageTexts.PAYMENT_SETUP.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSetupKeyboard.get_keyboard(custom_bot.bot_id,
                                                                           custom_bot.options_id,
                                                                           stars)
            )
        case callback_data.ActionEnum.SET_PROVIDER_TOKEN:
            await _send_provider_token_instructions(query.from_user.id)
            state_data = await state.get_data()
            await query.message.answer(
                "Введите Provider Token: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await state.set_state(States.SETTING_PROVIDER_TOKEN)
            await state.set_data(state_data)
        case callback_data.ActionEnum.SHOW_PAYMENT:
            if custom_bot.payment_type == BotPaymentTypeValues.TG_PROVIDER and not custom_bot.provider_token:
                return await query.answer("⚠️ Вы не указали provider token в настройках платежей."
                                          "\n\nБез этого параметра платежи не будут работать.",
                                          show_alert=True)
            if custom_bot.payment_type == BotPaymentTypeValues.TG_PROVIDER:
                await query.message.answer("Данные для тестовой оплаты:"
                                           "\n\n💳 Номер карты:\n<code>4242 4242 4242 4242</code>"
                                           "\n\n📆 Годна до:\n<code>12/30</code>"
                                           f"\n\n*️⃣ CVC:\n<code>111</code>")
            await query.message.answer_invoice(**(await create_invoice_params(custom_bot.bot_id,
                                                                              query.from_user.id,
                                                                              order_items={},
                                                                              test=True,
                                                                              order_id="TEST",
                                                                              )))
            await query.answer()
        case callback_data.ActionEnum.SEND_TO_BOT:
            if custom_bot.payment_type == BotPaymentTypeValues.TG_PROVIDER and not custom_bot.provider_token:
                return await query.answer("⚠️ Вы не указали provider token в настройках платежей."
                                          "\n\nБез этого параметра платежи не будут работать.",
                                          show_alert=True)
            try:
                await custom_bot_tg.send_message(
                    chat_id=query.from_user.id,
                    text=MessageTexts.SEND_PAYMENT_SHOW_TO_CUSTOM_BOT.value
                )
                await custom_bot_tg.send_invoice(
                    chat_id=query.from_user.id,
                    **(await create_invoice_params(
                        bot_id=custom_bot.bot_id,
                        user_id=query.from_user.id,
                        order_items={},
                        test=True,
                        user_bot_test=True,
                        order_id="TEST"
                    ))
                )
                if 'LIVE' in custom_bot.provider_token:
                    await custom_bot_tg.send_message(
                        chat_id=query.from_user.id,
                        text="⚠️ У Вас подключен рабочий provider token, деньги за этот платёж будут реально списаны."
                    )
                else:
                    if custom_bot.payment_type == BotPaymentTypeValues.TG_PROVIDER:
                        await query.message.answer("Данные для тестовой оплаты:"
                                                   "\n\n💳 Номер карты:\n<code>4242 4242 4242 4242</code>"
                                                   "\n\n📆 Годна до:\n<code>12/30</code>"
                                                   f"\n\n*️⃣ CVC:\n<code>111</code>")
                if custom_bot.payment_type == BotPaymentTypeValues.STARS:
                    await custom_bot_tg.send_message(
                        chat_id=query.from_user.id,
                        text="⚠️ У Вас подключена оплата звездами, звезды будут реально списаны "
                             "при оплате тестового платежа.."
                    )
                await query.answer("Платеж отправлен в Вашего бота.")
            except TelegramBadRequest as ex:
                if "chat not found" in str(ex):
                    return await query.answer("⚠️ Вы ни разу не писали своему боту."
                                              "\n\nОн не может отправить Вам сообщение первым.",
                                              show_alert=True)
                if "CURRENCY_INVALID" in str(ex):
                    return await query.answer(f"⚠️ Указанная Вами валюта ({custom_bot_options.currency_symbol.value}) "
                                              f"не поддерживается платежным провайдером, чей токен Вы указали.",
                                              show_alert=True)
                if "PAYMENT_PROVIDER_INVALID" in str(ex):
                    return await query.answer(f"⚠️ Указанный Вами Provider Token не действует."
                                              f"\n\nПерепроверьте правильность написания и добавьте его еще раз, "
                                              f"если это не помогло, обратитесь к своему платёжному провайдеру.",
                                              show_alert=True)
                else:
                    raise ex
        case callback_data.ActionEnum.BACK_TO_PAYMENT_MENU:
            await query.message.edit_text(
                MessageTexts.PAYMENT_METHOD_SETTINGS.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSettingsKeyboard.get_keyboard(custom_bot.bot_id,
                                                                              custom_bot.payment_type)
            )


@custom_bot_editing_router.callback_query(
    lambda query: InlineCurrencySelectKeyboard.callback_validator(query.data)
)
async def select_currency_settings(query: CallbackQuery, state: FSMContext):
    callback_data = InlineCurrencySelectKeyboard.Callback.model_validate_json(query.data)

    custom_bot = await bot_db.get_bot(callback_data.bot_id)
    custom_bot_data = await Bot(custom_bot.token).get_me()
    custom_bot_options = await option_db.get_option(custom_bot.options_id)

    if custom_bot.payment_type == BotPaymentTypeValues.STARS:
        await query.answer("⚠️ При выборе оплаты звездами, нет необходимости указывать валюту.",
                           show_alert=True)
        return await query.message.edit_text(
            MessageTexts.PAYMENT_METHOD_SETTINGS.value.format(custom_bot_data.username),
            reply_markup=await InlinePaymentSettingsKeyboard.get_keyboard(custom_bot.bot_id,
                                                                          custom_bot.payment_type)
        )

    match callback_data.a:
        case callback_data.ActionEnum.RUB:
            custom_bot_options.currency_code = CurrencyCodesValues.RUSSIAN_RUBLE
            custom_bot_options.currency_symbol = CurrencySymbolsValues.RUSSIAN_RUBLE
            await option_db.update_option(custom_bot_options)
            await query.answer(f"💱 Российский рубль ({CurrencySymbolsValues.RUSSIAN_RUBLE.value}) "
                               f"\nвыбран валютой магазина.", show_alert=True)
            return await query.message.edit_text(
                MessageTexts.CURRENCY_SELECT_TEXT.value.format(custom_bot_data.username),
                reply_markup=await InlineCurrencySelectKeyboard.get_keyboard(callback_data.bot_id,
                                                                             custom_bot_options.currency_code)
            )
        case callback_data.ActionEnum.EUR:
            custom_bot_options.currency_code = CurrencyCodesValues.EURO
            custom_bot_options.currency_symbol = CurrencySymbolsValues.EURO
            await option_db.update_option(custom_bot_options)
            await query.answer(f"💱 Евро ({CurrencySymbolsValues.EURO.value}) "
                               f"\nвыбран валютой магазина.", show_alert=True)
            return await query.message.edit_text(
                MessageTexts.CURRENCY_SELECT_TEXT.value.format(custom_bot_data.username),
                reply_markup=await InlineCurrencySelectKeyboard.get_keyboard(callback_data.bot_id,
                                                                             custom_bot_options.currency_code)
            )
        case callback_data.ActionEnum.USD:
            custom_bot_options.currency_code = CurrencyCodesValues.US_DOLLAR
            custom_bot_options.currency_symbol = CurrencySymbolsValues.US_DOLLAR
            await option_db.update_option(custom_bot_options)
            await query.answer(f"💱 Доллар США ({CurrencySymbolsValues.US_DOLLAR.value}) "
                               f"\nвыбран валютой магазина.", show_alert=True)
            return await query.message.edit_text(
                MessageTexts.CURRENCY_SELECT_TEXT.value.format(custom_bot_data.username),
                reply_markup=await InlineCurrencySelectKeyboard.get_keyboard(callback_data.bot_id,
                                                                             custom_bot_options.currency_code)
            )
        case callback_data.ActionEnum.ISL:
            custom_bot_options.currency_code = CurrencyCodesValues.ISRAELI_SHEQEL
            custom_bot_options.currency_symbol = CurrencySymbolsValues.ISRAELI_SHEQEL
            await option_db.update_option(custom_bot_options)
            await query.answer(f"💱 Израильский шекель ({CurrencySymbolsValues.ISRAELI_SHEQEL.value}) "
                               f"\nвыбран валютой магазина.", show_alert=True)
            return await query.message.edit_text(
                MessageTexts.CURRENCY_SELECT_TEXT.value.format(custom_bot_data.username),
                reply_markup=await InlineCurrencySelectKeyboard.get_keyboard(callback_data.bot_id,
                                                                             custom_bot_options.currency_code)
            )
        case callback_data.ActionEnum.BACK_TO_PAYMENT_MENU:
            await query.message.edit_text(
                MessageTexts.PAYMENT_METHOD_SETTINGS.value.format(custom_bot_data.username),
                reply_markup=await InlinePaymentSettingsKeyboard.get_keyboard(custom_bot.bot_id,
                                                                              custom_bot.payment_type)
            )


@custom_bot_editing_router.callback_query(
    lambda query: InlineBotEditOrderOptionsKeyboard.callback_validator(query.data)
)
async def manage_order_options(query: CallbackQuery, state: FSMContext):
    callback_data = InlineBotEditOrderOptionsKeyboard.Callback.model_validate_json(query.data)

    custom_bot = await bot_db.get_bot(callback_data.bot_id)
    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_BOT_MENU:
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(callback_data.bot_id)
            )
        case callback_data.ActionEnum.ADD_ORDER_OPTION:
            await query.message.answer(
                "Введите название новой опции: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.WAITING_FOR_NEW_ORDER_OPTION_TEXT)
            await state.set_data({"bot_id": callback_data.bot_id})
        case callback_data.ActionEnum.EDIT_ORDER_OPTION:
            try:
                oo = await order_option_db.get_order_option(callback_data.order_option_id)
            except OrderOptionNotFoundError:
                await query.answer("Вы уже удалили эту опцию", show_alert=True)
                await query.message.delete()
                return
            await query.message.edit_text(
                **MessageTexts.generate_order_option_info(oo),
                reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(
                    custom_bot.bot_id, callback_data.order_option_id
                )
            )
            await query.answer()


@custom_bot_editing_router.callback_query(lambda query: InlineBotEditOrderOptionKeyboard.callback_validator(query.data))
async def manage_order_option(query: CallbackQuery, state: FSMContext):
    callback_data = InlineBotEditOrderOptionKeyboard.Callback.model_validate_json(query.data)

    custom_bot = await bot_db.get_bot(callback_data.bot_id)

    order_options = await order_option_db.get_all_order_options(custom_bot.bot_id)

    sorted_oo = sorted(order_options, key=lambda x: x.position_index)

    try:
        order_option = await order_option_db.get_order_option(callback_data.order_option_id)
    except OrderOptionNotFoundError:
        await query.answer("Эта опция уже удалена", show_alert=True)
        await query.message.delete()
        return

    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_ORDER_OPTIONS:
            await query.message.edit_text(
                **MessageTexts.generate_order_options_info(order_options),
                reply_markup=await InlineBotEditOrderOptionsKeyboard.get_keyboard(custom_bot.bot_id)
            )

        case callback_data.ActionEnum.EDIT_REQUIRED_STATUS:
            order_option.required = not order_option.required
            await order_option_db.update_order_option(order_option)
            await query.message.edit_reply_markup(
                reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(
                    custom_bot.bot_id, callback_data.order_option_id
                )
            )

        case callback_data.ActionEnum.EDIT_EMOJI:
            await query.message.answer(
                "Введите новый эмодзи к этой опции: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.WAITING_FOR_ORDER_OPTION_EMOJI)
            await state.set_data({"bot_id": callback_data.bot_id, "order_option_id": callback_data.order_option_id})

        case callback_data.ActionEnum.EDIT_OPTION_NAME:
            await query.message.answer(
                "Введите новый текст к этой опции: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.WAITING_FOR_ORDER_OPTION_TEXT)
            await state.set_data({"bot_id": callback_data.bot_id, "order_option_id": callback_data.order_option_id})
        case callback_data.ActionEnum.EDIT_POSITION_INDEX:
            await query.message.answer(
                "Введите номер позиции к этой опции: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.WAITING_FOR_ORDER_OPTION_POSITION)
            await state.set_data({"bot_id": callback_data.bot_id, "order_option_id": callback_data.order_option_id})

        case callback_data.ActionEnum.EDIT_ORDER_OPTION_TYPE:
            await query.message.edit_text(
                f"Текущий тип опции - {order_option.option_type.value}",
                reply_markup=await InlineEditOrderOptionTypeKeyboard.get_keyboard(
                    callback_data.bot_id, callback_data.order_option_id))

        case callback_data.ActionEnum.DELETE_ORDER_OPTION:

            await order_option_db.delete_order_option(order_option.id)
            sorted_oo.remove(order_option)
            for index, option in enumerate(sorted_oo):
                option.position_index = index + 1
                await order_option_db.update_order_option(option)
            await query.answer("Опция удалена", show_alert=True)
            await query.message.edit_text(
                **MessageTexts.generate_order_options_info(sorted_oo),
                reply_markup=await InlineBotEditOrderOptionsKeyboard.get_keyboard(custom_bot.bot_id)
            )


@custom_bot_editing_router.callback_query(
    lambda query: InlineEditOrderOptionTypeKeyboard.callback_validator(query.data)
)
async def edit_order_option_type_menu(query: CallbackQuery, state: FSMContext):
    callback_data = InlineEditOrderOptionTypeKeyboard.Callback.model_validate_json(query.data)

    try:
        order_option = await order_option_db.get_order_option(callback_data.opt_id)
    except OrderOptionNotFoundError:
        await query.answer("Эта опция уже удалена", show_alert=True)
        await query.message.delete()
        return

    match callback_data.a:
        case callback_data.ActionEnum.EDIT_OPTION_TYPE:
            if order_option.option_type.value == OrderOptionTypeValues.TEXT.value:
                order_option.option_type = OrderOptionTypeValues.CHOOSE
            else:
                order_option.option_type = OrderOptionTypeValues.TEXT
            await order_option_db.update_order_option(order_option)
            await query.message.edit_text(
                f"Текущий тип опции - {order_option.option_type.value}",
                reply_markup=await InlineEditOrderOptionTypeKeyboard.get_keyboard(
                    callback_data.bot_id, callback_data.opt_id)
            )

        case callback_data.ActionEnum.ADD_CHOOSE_OPTION:
            if order_option.option_type.value == OrderOptionTypeValues.TEXT.value:
                return await query.answer("Текущий тип опции простой текст!", show_alert=True)
            await query.message.answer(
                "Введите название варианта ответа",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.WAITING_FOR_NEW_ORDER_CHOOSE_OPTION_TEXT)
            await state.set_data({"bot_id": callback_data.bot_id, "order_option_id": callback_data.opt_id})

        case callback_data.ActionEnum.EDIT_CHOOSE_OPTION:
            if order_option.option_type.value == OrderOptionTypeValues.TEXT.value:
                return await query.answer("Текущий тип опции простой текст!", show_alert=True)
            choose_option = await order_choose_option_db.get_choose_option(callback_data.choose_id)
            await query.message.edit_text(
                f"Меню редактирования варианта ответа {choose_option.choose_option_name}",
                reply_markup=InlineEditOrderChooseOptionKeyboard.get_keyboard(
                    callback_data.bot_id, callback_data.opt_id, callback_data.choose_id))

        case callback_data.ActionEnum.BACK_TO_ORDER_OPTION:
            await query.message.edit_text(
                **MessageTexts.generate_order_option_info(order_option),
                reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(
                    callback_data.bot_id, callback_data.opt_id
                )
            )


@custom_bot_editing_router.callback_query(
    lambda query: InlineEditOrderChooseOptionKeyboard.callback_validator(query.data)
)
async def manage_order_choose_option(query: CallbackQuery, state: FSMContext):
    callback_data = InlineEditOrderChooseOptionKeyboard.Callback.model_validate_json(query.data)

    try:
        order_option = await order_option_db.get_order_option(callback_data.opt_id)
    except OrderOptionNotFoundError:
        await query.answer("Эта опция уже удалена", show_alert=True)
        await query.message.delete()
        return

    if order_option.option_type.value == OrderOptionTypeValues.TEXT.value:
        return await query.answer("Текущий тип опции простой текст!", show_alert=True)

    try:
        await order_choose_option_db.get_choose_option(callback_data.choose_id)
    except OrderOptionNotFoundError:
        await query.answer("Этот вариант ответа уже удален", show_alert=True)
        await query.message.delete()
        return

    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_ORDER_TYPE_MENU:
            await query.message.edit_text(
                f"Текущий тип опции - {order_option.option_type.value}",
                reply_markup=await InlineEditOrderOptionTypeKeyboard.get_keyboard(
                    callback_data.bot_id, callback_data.opt_id)
            )

        case callback_data.ActionEnum.EDIT_CHOOSE_OPTION_NAME:
            await query.message.answer(
                "Введите новое название варианта ответа",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await state.set_state(States.WAITING_FOR_ORDER_CHOOSE_OPTION_TEXT)
            await state.set_data(
                {
                    "bot_id": callback_data.bot_id,
                    "order_option_id": callback_data.opt_id,
                    "order_choose_option_id": callback_data.choose_id
                }
            )

        case callback_data.ActionEnum.DELETE_CHOOSE_OPTION:
            await order_choose_option_db.delete_choose_option(callback_data.choose_id)

            await query.answer("Вариант ответа удален!", show_alert=True)

            await query.message.edit_text(
                f"Текущий тип опции - {order_option.option_type.value}",
                reply_markup=await InlineEditOrderOptionTypeKeyboard.get_keyboard(
                    callback_data.bot_id, callback_data.opt_id)
            )


@custom_bot_editing_router.message(States.WAITING_FOR_ORDER_CHOOSE_OPTION_TEXT)
async def edit_choose_option_name(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()

        bot_id = state_data['bot_id']
        custom_bot = await bot_db.get_bot(bot_id)
        order_option = await order_option_db.get_order_option(state_data["order_option_id"])
        choose_option = await order_choose_option_db.get_choose_option(state_data["order_choose_option_id"])

        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=bot_id)
                )
                await message.answer(
                    f"Меню редактирования варианта ответа {choose_option.choose_option_name}",
                    reply_markup=InlineEditOrderChooseOptionKeyboard.get_keyboard(
                        custom_bot.bot_id, order_option.id, choose_option.id))
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)

            case _:
                choose_option.choose_option_name = message.text

                await order_choose_option_db.update_choose_option(choose_option)

                await message.answer(
                    "Текст варианта ответа изменен!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
                )
                await message.answer(
                    f"Меню редактирования варианта ответа {choose_option.choose_option_name}",
                    reply_markup=InlineEditOrderChooseOptionKeyboard.get_keyboard(
                        custom_bot.bot_id, order_option.id, choose_option.id))
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Сообщение должно содержать текст")


@custom_bot_editing_router.message(States.SETTING_PROVIDER_TOKEN)
async def handle_provider_token_input(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()

        bot_id = state_data['bot_id']
        custom_bot = await bot_db.get_bot(bot_id)
        custom_bot_data = await Bot(custom_bot.token).get_me()

        if custom_bot.payment_type == BotPaymentTypeValues.STARS:
            stars = True
        else:
            stars = False

        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в настройки платежа...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
                return await message.answer(
                    MessageTexts.PAYMENT_SETUP.value.format(custom_bot_data.username),
                    reply_markup=await InlinePaymentSetupKeyboard.get_keyboard(custom_bot.bot_id,
                                                                               custom_bot.options_id,
                                                                               stars)
                )
            case _:
                params = message.text.strip().split(':')
                params = message.text.strip().split(':')
                if len(params) != 3:
                    return await message.answer("Неверный формат токена.\n\nФормат ожидаемого токена:"
                                                "\nДля тестовой оплаты:"
                                                "\n<code>1149974399:TEST:3b592a9aaa1b54e58daa</code>"
                                                "\nДля рабочей оплаты:"
                                                "\n<code>1149974399:LIVE:3b592a9aaa1b54e58daa</code>")
                if params[1] == "LIVE":
                    await message.answer("Вы подключили токен для <b><u>рабочей</u></b> оплаты.")
                elif params[1] == "TEST":
                    await message.answer("Вы подключили токен для <b><u>тестовой</u></b> оплаты.")
                else:
                    return await message.answer("Неверный формат токена.\n\nФормат ожидаемого токена:"
                                                "\nДля тестовой оплаты:"
                                                "\n<code>1149974399:TEST:3b592a9aaa1b54e58daa</code>"
                                                "\nДля рабочей оплаты:"
                                                "\n<code>1149974399:LIVE:3b592a9aaa1b54e58daa</code>")
                custom_bot.provider_token = message.text.strip()
                await bot_db.update_bot(custom_bot)
                return await message.answer(
                    MessageTexts.PAYMENT_SETUP.value.format(custom_bot_data.username),
                    reply_markup=await InlinePaymentSetupKeyboard.get_keyboard(custom_bot.bot_id,
                                                                               custom_bot.options_id,
                                                                               stars)
                )
    else:
        await message.answer("Необходимо отправить Provider Token в тексте сообщения")


@custom_bot_editing_router.message(States.WAITING_FOR_NEW_ORDER_CHOOSE_OPTION_TEXT)
async def make_new_choose_option(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()

        bot_id = state_data['bot_id']
        custom_bot = await bot_db.get_bot(bot_id)
        order_option = await order_option_db.get_order_option(state_data["order_option_id"])

        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=bot_id)
                )
                await message.answer(
                    f"Текущий тип опции - {order_option.option_type.value}",
                    reply_markup=await InlineEditOrderOptionTypeKeyboard.get_keyboard(
                        custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                await order_choose_option_db.add_choose_option(
                    OrderChooseOptionSchemaWithoutId(
                        order_option_id=order_option.id,
                        choose_option_name=message.text
                    )
                )
                await message.answer(
                    "Новая вариант ответа опции на выбор был добавлен",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
                )
                await message.answer(
                    f"Текущий тип опции - {order_option.option_type.value}",
                    reply_markup=await InlineEditOrderOptionTypeKeyboard.get_keyboard(
                        custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)

    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.WAITING_FOR_ORDER_OPTION_POSITION)
async def edit_order_option_position(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])
        order_option = await order_option_db.get_order_option(state_data["order_option_id"])
        order_options = await order_option_db.get_all_order_options(custom_bot.bot_id)
        sorted_oo = sorted(order_options, key=lambda x: x.position_index)
        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    **MessageTexts.generate_order_option_info(order_option),
                    reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                try:
                    index = int(message.text)
                except ValueError:
                    return await message.answer("В сообщении должно  быть только число")
                if index <= 0:
                    return await message.answer("Номер позиции должен быть больше 0")
                if index > sorted_oo[-1].position_index:
                    return await message.answer("У вас нет столько опций")
                sorted_oo.remove(order_option)
                sorted_oo.insert(index - 1, order_option)
                for i, option in enumerate(sorted_oo):
                    option.position_index = i + 1
                    await order_option_db.update_order_option(option)
                await message.answer(
                    "Новая позиция опции добавлена",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=custom_bot.bot_id)
                )
                await message.answer(
                    **MessageTexts.generate_order_option_info(order_option),
                    reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)

    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.WAITING_FOR_ORDER_OPTION_TEXT)
async def edit_order_option_name(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])
        order_option = await order_option_db.get_order_option(state_data["order_option_id"])
        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    **MessageTexts.generate_order_option_info(order_option),
                    reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                order_option.option_name = message.text
                await order_option_db.update_order_option(order_option)
                await message.answer(
                    "Новое название опции добавлено",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=custom_bot.bot_id)
                )
                await message.answer(
                    **MessageTexts.generate_order_option_info(order_option),
                    reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)

    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.WAITING_FOR_ORDER_OPTION_EMOJI)
async def edit_order_option_emoji(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])
        order_option = await order_option_db.get_order_option(state_data["order_option_id"])
        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    **MessageTexts.generate_order_option_info(order_option),
                    reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                emoji_pattern = re.compile(
                    r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-'
                    r'\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-'
                    r'\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-'
                    r'\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]$'
                )
                if emoji_pattern.match(message.text):
                    order_option.emoji = message.text
                    await order_option_db.update_order_option(order_option)
                    await message.answer(
                        "Новый эмодзи добавлен",
                        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=custom_bot.bot_id)
                    )
                    await message.answer(
                        **MessageTexts.generate_order_option_info(order_option),
                        reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(
                            custom_bot.bot_id, order_option.id
                        )
                    )
                    await state.set_state(States.BOT_MENU)
                    await state.set_data(state_data)
                else:
                    await message.answer("Сообщение должно содержать эмодзи")

    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.WAITING_FOR_NEW_ORDER_OPTION_TEXT)
async def create_new_order_option(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()

        bot_id = state_data["bot_id"]
        custom_bot = await bot_db.get_bot(bot_id)
        order_options = await order_option_db.get_all_order_options(custom_bot.bot_id)
        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=bot_id)
                )
                await message.answer(
                    **MessageTexts.generate_order_options_info(order_options),
                    reply_markup=await InlineBotEditOrderOptionsKeyboard.get_keyboard(custom_bot.bot_id)
                )

                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                sorted_oo = sorted(order_options, key=lambda x: x.position_index)

                if len(sorted_oo) == 0:
                    pos_ind = 1
                else:
                    pos_ind = (sorted_oo[-1].position_index + 1)
                await order_option_db.add_order_option(
                    OrderOptionSchemaWithoutId(
                        bot_id=custom_bot.bot_id,
                        option_name=message.text,
                        position_index=pos_ind
                    )
                )
                await message.answer(
                    "Новая опция успешно добавлена!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=bot_id)
                )
                order_options = await order_option_db.get_all_order_options(custom_bot.bot_id)
                await message.answer(
                    **MessageTexts.generate_order_options_info(order_options),
                    reply_markup=await InlineBotEditOrderOptionsKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)

    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.EDITING_START_MESSAGE)
async def editing_start_message_handler(message: Message, state: FSMContext):
    """Настраивает стартовое сообщение кастомного бота"""

    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                try:
                    options = await option_db.get_option(custom_bot.options_id)
                except OptionNotFoundError:
                    new_options_id = await create_bot_options()
                    custom_bot.options_id = new_options_id
                    await bot_db.update_bot(custom_bot)
                    options = await option_db.get_option(new_options_id)
                options.start_msg = message_text
                await option_db.update_option(options)

                await message.answer(
                    "Стартовое сообщение изменено!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )

                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.EDITING_DEFAULT_MESSAGE)
async def editing_default_message_handler(message: Message, state: FSMContext):
    """Настраивает дефолтное сообщение кастомного бота"""

    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message_text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                try:
                    options = await option_db.get_option(custom_bot.options_id)
                except OptionNotFoundError:
                    new_options_id = await create_bot_options()
                    custom_bot.options_id = new_options_id
                    await bot_db.update_bot(custom_bot)
                    options = await option_db.get_option(new_options_id)
                options.default_msg = message_text
                await option_db.update_option(options)

                await message.answer(
                    "Сообщение-затычка изменена!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Сообщение-затычка должна содержать текст")


@custom_bot_editing_router.message(States.EDITING_BG_COLOR)
async def editing_bg_color_handler(message: Message, state: FSMContext):
    """Настраивает bg_color веб приложения магазина"""

    message_text = message.text.strip()
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message_text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                if not _is_valid_hex_code(message_text) and message_text != "telegram":
                    return await message.answer("Не получилось распознать ввод. Введите еще раз цвет в формате "
                                                "<i>#FFFFFF</i> или напишите <i>telegram</i> для дефолтных цветов.")

                bg_color = None if message_text == "telegram" else message_text

                try:
                    options = await option_db.get_option(custom_bot.options_id)
                except OptionNotFoundError:
                    new_options_id = await create_bot_options()
                    custom_bot.options_id = new_options_id
                    await bot_db.update_bot(custom_bot)
                    options = await option_db.get_option(new_options_id)
                options.bg_color = bg_color
                await option_db.update_option(options)

                await message.answer(
                    "Цвет фона изменен!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Цвет должен быть указан в тексте сообщения.")


@custom_bot_editing_router.message(States.EDITING_POST_ORDER_MESSAGE)
async def editing_post_order_message_handler(message: Message, state: FSMContext):
    """Настраивает сообщение, которое будет отправляться клиентам после оформления заказа"""

    message_text = message.html_text
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message_text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в главное меню...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                try:
                    options = await option_db.get_option(custom_bot.options_id)
                except OptionNotFoundError:
                    new_options_id = await create_bot_options()
                    custom_bot.options_id = new_options_id
                    await bot_db.update_bot(custom_bot)
                    options = await option_db.get_option(new_options_id)
                options.post_order_msg = message_text
                await option_db.update_option(options)

                await message.answer(
                    "Сообщение после заказа изменено!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Сообщение должно содержать текст")


@custom_bot_editing_router.message(States.DELETE_BOT)
async def delete_bot_handler(message: Message, state: FSMContext):
    """Обрабатывает подтверждение удаления бота"""

    message_text = message.text
    state_data = await state.get_data()
    custom_bot = await bot_db.get_bot(state_data['bot_id'])

    match message_text:
        case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
            await message.answer(
                "Возвращаемся в главное меню...",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)

        case "ПОДТВЕРДИТЬ":
            logger.info(f"Disabling bot {state_data['bot_id']}, setting deleted status to db...")
            custom_bot.status = "Deleted"
            await bot_db.del_bot(custom_bot.bot_id)

            await message.answer(
                "Бот удален",
                reply_markup=ReplyKeyboardRemove()
            )
            await send_instructions(bot, None, message.from_user.id, cache_resources_file_id_store)
            await state.set_state(States.WAITING_FOR_TOKEN)
            await state.set_data({"bot_id": -1})

        case _:
            await message.answer("Напишите ПОДТВЕРДИТЬ для подтверждения удаления или вернитесь назад")
