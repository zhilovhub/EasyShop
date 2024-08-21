from datetime import datetime

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.main import stock_manager, bot
from bot.stoke.stoke import UnknownFileExtensionError
from bot.utils import MessageTexts
from bot.states import States
from bot.handlers.routers import stock_menu_router
from bot.utils.excel_utils import send_demo_import_xlsx, send_products_info_xlsx
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard
from bot.keyboards.stock_menu_keyboards import (
    InlineStockImportConfirmKeyboard,
    InlineStockImportFileTypeKeyboard,
    InlineStockMenuKeyboard,
    ReplyBackStockMenuKeyboard,
    InlineStockImportMenuKeyboard,
)
from common_utils.bot_utils import create_bot_options

from common_utils.config import common_settings
from common_utils.keyboards.keyboards import InlineBotMenuKeyboard

from database.config import product_db, bot_db, option_db
from database.models.option_model import OptionNotFoundError

from logs.config import logger, extra_params


@stock_menu_router.callback_query(lambda query: InlineStockMenuKeyboard.callback_validator(query.data))
async def stock_menu_handler(query: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатия на кнопки в меню настроек склада"""

    callback_data = InlineStockMenuKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id

    bot_data = await bot_db.get_bot(bot_id)
    try:
        options = await option_db.get_option(bot_data.options_id)
    except OptionNotFoundError:
        new_options_id = await create_bot_options()
        bot_data.options_id = new_options_id
        await bot_db.update_bot(bot_data)
        options = await option_db.get_option(new_options_id)

    match callback_data.a:
        case callback_data.ActionEnum.GOODS_COUNT:
            products = await product_db.get_all_products(bot_id)
            await query.message.answer(f"Количество товаров: {len(products)}")
            await query.answer()
        case callback_data.ActionEnum.ADD_GOOD:
            await query.message.answer(
                "Чтобы добавить товар, прикрепите его картинку и отправьте сообщение в виде:"
                "\n\nНазвание\nЦена в рублях"
            )
            await query.answer()
        case callback_data.ActionEnum.GOODS_COUNT_MANAGE:
            if await _check_goods_exist(query, bot_id, with_pictures=False):
                await query.message.answer(
                    MessageTexts.GOODS_COUNT_MESSAGE.value, reply_markup=ReplyBackStockMenuKeyboard.get_keyboard()
                )

                await state.set_state(States.GOODS_COUNT_MANAGE)
                await state.set_data({"bot_id": bot_id})

        case callback_data.ActionEnum.AUTO_REDUCE:
            options.auto_reduce = not options.auto_reduce
            await option_db.update_option(options)
            if options.auto_reduce:
                await query.message.answer("✅ Автоуменьшение кол-ва товаров после заказа <b>включено</b>.")
            else:
                await query.message.answer("❌ Автоуменьшение кол-ва товаров после заказа <b>выключено</b>.")
            try:
                await query.message.edit_text(
                    query.message.text,
                    reply_markup=await InlineStockMenuKeyboard.get_keyboard(bot_id, options.auto_reduce),
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                logger.error(
                    f"user_id={query.from_user.id}: TODO handle telegram api error message not modified",
                    extra=extra_params(user_id=query.from_user.id, bot_id=bot_id),
                    exc_info=e,
                )
        case callback_data.ActionEnum.IMPORT:
            await query.message.edit_text(
                MessageTexts.STOCK_IMPORT_COMMANDS.value,
                reply_markup=InlineStockImportMenuKeyboard.get_keyboard(bot_id),
                parse_mode=ParseMode.HTML,
            )
        case callback_data.ActionEnum.EXPORT:
            if await _check_goods_exist(query, bot_id, with_pictures=True):
                await query.message.answer(
                    "Меню склада:", reply_markup=await InlineStockMenuKeyboard.get_keyboard(bot_id, options.auto_reduce)
                )

        case callback_data.ActionEnum.BACK_TO_BOT_MENU:
            custom_bot = await bot_db.get_bot(bot_id)
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, query.from_user.id),
            )


@stock_menu_router.callback_query(lambda query: InlineStockImportMenuKeyboard.callback_validator(query.data))
async def import_menu_handler(query: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатия на кнопки при импорте товаров"""

    callback_data = InlineStockImportMenuKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id
    bot_data = await bot_db.get_bot(bot_id)
    try:
        options = await option_db.get_option(bot_data.options_id)
    except OptionNotFoundError:
        new_options_id = await create_bot_options()
        bot_data.options_id = new_options_id
        await bot_db.update_bot(bot_data)
        options = await option_db.get_option(new_options_id)

    if callback_data.a == callback_data.ActionEnum.BACK_TO_STOCK_MENU:
        return await query.message.edit_text(
            "Меню склада:",
            reply_markup=await InlineStockMenuKeyboard.get_keyboard(bot_id, options.auto_reduce),
            parse_mode=ParseMode.HTML,
        )

    await query.message.edit_text(
        text=MessageTexts.STOCK_IMPORT_FILE_TYPE.value,
        reply_markup=InlineStockImportFileTypeKeyboard.get_keyboard(bot_id, callback_data.a.value),
    )
    await state.set_data({"bot_id": bot_id})


@stock_menu_router.callback_query(lambda query: InlineStockImportFileTypeKeyboard.callback_validator(query.data))
async def pick_import_file_type(query: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор типа импортируемого файла: xlsx,"""

    callback_data = InlineStockImportFileTypeKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id
    import_action = callback_data.import_action

    if callback_data.a == callback_data.ActionEnum.BACK_TO_STOCK_MENU:
        return await query.message.edit_text(
            text=MessageTexts.STOCK_IMPORT_COMMANDS.value,
            reply_markup=InlineStockImportMenuKeyboard.get_keyboard(bot_id),
            parse_mode=ParseMode.HTML,
        )

    match callback_data.a:
        case callback_data.ActionEnum.EXCEL:
            example_file = send_demo_import_xlsx
        case _:
            raise UnknownFileExtensionError(callback_data.a.value)

    await query.message.answer(
        "Теперь отправьте боту xlsx файл с товарами в таком же формате, как файл ниже",
        reply_markup=ReplyBackStockMenuKeyboard.get_keyboard(),
    )

    await example_file(bot_id)

    await state.set_state(States.IMPORT_PRODUCTS)
    await state.set_data({"bot_id": bot_id, "file_type": callback_data.a.value, "import_action": import_action})


@stock_menu_router.message(States.GOODS_COUNT_MANAGE)
async def handle_stock_manage_input(message: Message, state: FSMContext):
    """Ожидает от пользователя xlsx файл с новыми остатками"""

    state_data = await state.get_data()
    if message.text == ReplyBackStockMenuKeyboard.Callback.ActionEnum.BACK_TO_STOCK_MENU.value:
        return await _back_to_stock_menu(message, state)

    if message.content_type != "document":
        return await message.answer(
            "Необходимо отправить xlsx файл с товарами", reply_markup=ReplyBackStockMenuKeyboard.get_keyboard()
        )

    file_extension = message.document.file_name.split(".")[-1].lower()

    if file_extension not in ("xlsx",):
        return await message.answer(
            "Файл должен быть в формате xlsx", reply_markup=ReplyBackStockMenuKeyboard.get_keyboard()
        )
    try:
        file_path = f"{common_settings.FILES_PATH}docs/{datetime.now().strftime('%d$m%Y_%H%M%S')}.{file_extension}"
        await bot.download(message.document.file_id, destination=file_path)

        status, err_message = await stock_manager.update_count_xlsx(file_path, state_data["bot_id"])
        if not status:
            return await message.answer(err_message)

        await message.answer("Кол-во товаров на складе обновлено")
        await _back_to_stock_menu(message, state)

    except Exception as e:
        logger.error(
            f"user_id={message.from_user.id}: TODO exception is not dispatched",
            extra=extra_params(user_id=message.from_user.id),
            exc_info=e,
        )
        raise e


@stock_menu_router.message(States.IMPORT_PRODUCTS)
async def handle_stock_import_input(message: Message, state: FSMContext):
    """Ожидает от пользователя xlsx файл с новыми товарами для импорта"""

    state_data = await state.get_data()

    bot_id = state_data["bot_id"]
    file_type = state_data["file_type"]
    import_action = state_data["import_action"]

    if message.text == ReplyBackStockMenuKeyboard.Callback.ActionEnum.BACK_TO_STOCK_MENU.value:
        await message.answer(
            text=MessageTexts.STOCK_IMPORT_FILE_TYPE.value,
            reply_markup=InlineStockImportFileTypeKeyboard.get_keyboard(bot_id=bot_id, import_action=import_action),
        )
        await message.answer(text="Возвращаемся назад...", reply_markup=ReplyBotMenuKeyboard.get_keyboard())
        await state.set_state(States.BOT_MENU)
        await state.set_data(state_data)
        return

    if message.content_type != "document":
        return await message.answer(
            "Необходимо отправить файл с товарами.", reply_markup=ReplyBackStockMenuKeyboard.get_keyboard()
        )

    file_extension = message.document.file_name.split(".")[-1].lower()

    match file_type:
        case InlineStockImportFileTypeKeyboard.Callback.ActionEnum.EXCEL.value:
            if file_extension not in ("xlsx",):
                return await message.answer(
                    "Файл должен быть в формате xlsx", reply_markup=ReplyBackStockMenuKeyboard.get_keyboard()
                )
        case _:
            raise UnknownFileExtensionError(file_type)

    try:
        file_path = f"{common_settings.FILES_PATH}docs/{datetime.now().strftime('%d$m%Y_%H%M%S')}.{file_extension}"
        await bot.download(message.document.file_id, destination=file_path)

        match file_extension:
            case "xlsx":
                status, err_message = await stock_manager.check_xlsx(file_path)
            case _:
                raise UnknownFileExtensionError(file_extension)

        if not status:
            return await message.answer(f"Файл не соответствует формату ({err_message})")

        await message.answer(
            text=MessageTexts.CONFIRM_STOCK_IMPORT.value,
            reply_markup=InlineStockImportConfirmKeyboard.get_keyboard(bot_id, import_action, file_type),
        )
        state_data["file_path"] = file_path
        await state.set_data(state_data)

    except Exception as e:
        user_id = message.from_user.id
        logger.error(f"user_id={user_id}: stock import failed", extra=extra_params(user_id=user_id), exc_info=e)
        raise e


@stock_menu_router.callback_query(lambda query: InlineStockImportConfirmKeyboard.callback_validator(query.data))
async def confirm_file_import(query: CallbackQuery, state: FSMContext):
    """Ожидает от пользователя подтверждение импорта товаров"""

    callback_data = InlineStockImportConfirmKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id
    file_type = callback_data.file_type
    import_action = callback_data.import_action

    state_data = await state.get_data()
    file_path = state_data["file_path"]

    match callback_data.a:
        case callback_data.ActionEnum.DENY:
            await query.message.delete()
            await query.message.answer(
                text=MessageTexts.STOCK_IMPORT_FILE_TYPE.value,
                reply_markup=InlineStockImportFileTypeKeyboard.get_keyboard(bot_id=bot_id, import_action=import_action),
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)
            return

        case callback_data.ActionEnum.CONFIRM:
            replace = False
            replace_d = False
            match import_action:
                case "replace_all":
                    replace = True
                case "replace_duplicates":
                    replace_d = True

            match file_type:
                case InlineStockImportFileTypeKeyboard.Callback.ActionEnum.EXCEL.value:
                    await stock_manager.import_xlsx(
                        bot_id=bot_id, path_to_file=file_path, replace=replace, replace_duplicates=replace_d
                    )
                case _:
                    raise UnknownFileExtensionError(file_type)

            await query.message.answer("Товары обновлены")
            await query.message.delete()

            await _back_to_stock_menu(query.message, state)


async def _back_to_stock_menu(message: Message, state: FSMContext) -> None:
    """Returns to stock menu from everywhere"""

    bot_id = (await state.get_data())["bot_id"]
    bot_data = await bot_db.get_bot(bot_id)
    try:
        options = await option_db.get_option(bot_data.options_id)
    except OptionNotFoundError:
        new_options_id = await create_bot_options()
        bot_data.options_id = new_options_id
        await bot_db.update_bot(bot_data)
        options = await option_db.get_option(new_options_id)

    await message.answer("Возвращаемся в меню склада...", reply_markup=ReplyBotMenuKeyboard.get_keyboard())
    await message.answer(
        "Меню склада:", reply_markup=await InlineStockMenuKeyboard.get_keyboard(bot_id, options.auto_reduce)
    )
    await state.set_state(States.BOT_MENU)
    await state.set_data({"bot_id": bot_id})


async def _check_goods_exist(query: CallbackQuery, bot_id: int, with_pictures: bool) -> bool:
    """Check whether there are goods or no"""

    products = await product_db.get_all_products(bot_id)
    if len(products) == 0:
        await query.answer("Товаров на складе нет")
        return False
    else:
        await send_products_info_xlsx(bot_id, products, with_pictures)
        await query.answer()
        return True
