from datetime import datetime

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.main import stock_manager, bot
from bot.utils import MessageTexts
from bot.states import States
from bot.handlers.routers import stock_menu_router
from bot.utils.excel_utils import send_products_info_xlsx
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard
from bot.keyboards.stock_menu_keyboards import InlineStockImportFileTypeKeyboard, InlineStockMenuKeyboard, ReplyBackStockMenuKeyboard, \
    InlineStockImportMenuKeyboard

from common_utils.env_config import FILES_PATH
from common_utils.keyboards.keyboards import InlineBotMenuKeyboard

from database.config import product_db, bot_db

from logs.config import logger, extra_params


@stock_menu_router.callback_query(lambda query: InlineStockMenuKeyboard.callback_validator(query.data))
async def stock_menu_handler(query: CallbackQuery, state: FSMContext):
    callback_data = InlineStockMenuKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id

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
            await query.message.edit_text(
                MessageTexts.GOODS_COUNT_MESSAGE.value,
                reply_markup=None
            )
            xlsx_file_path, photo_path = await stock_manager.export_xlsx(bot_id=bot_id, with_pictures=False)
            await query.message.answer_document(document=FSInputFile(xlsx_file_path),
                                                caption="Список товаров на складе",
                                                reply_markup=ReplyBackStockMenuKeyboard.get_keyboard())

            await state.set_state(States.GOODS_COUNT_MANAGE)
            await state.set_data({'bot_id': bot_id})
        case callback_data.ActionEnum.AUTO_REDUCE:
            bot_data = await bot_db.get_bot(bot_id)
            if not bot_data.settings:
                bot_data.settings = {}
            if "auto_reduce" not in bot_data.settings:
                bot_data.settings["auto_reduce"] = True
            else:
                bot_data.settings["auto_reduce"] = not bot_data.settings["auto_reduce"]
            await bot_db.update_bot(bot_data)
            if bot_data.settings["auto_reduce"]:
                await query.message.answer("✅ Автоуменьшение кол-ва товаров после заказа <b>включено</b>.")
            else:
                await query.message.answer("❌ Автоуменьшение кол-ва товаров после заказа <b>выключено</b>.")
            try:
                await query.message.edit_text(
                    query.message.text,
                    reply_markup=await InlineStockMenuKeyboard.get_keyboard(bot_id, bot_data.settings["auto_reduce"]),
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                # TODO handle telegram api error "message not modified"
                logger.error(
                    f"user_id={query.from_user.id}: TODO handle telegram api error message not modified",
                    extra=extra_params(user_id=query.from_user.id, bot_id=bot_id),
                    exc_info=e
                )
        case callback_data.ActionEnum.IMPORT:
            await query.message.edit_text(
                MessageTexts.STOCK_IMPORT_COMMANDS.value,
                reply_markup=InlineStockImportMenuKeyboard.get_keyboard(bot_id),
                parse_mode=ParseMode.HTML
            )
        case callback_data.ActionEnum.EXPORT:
            bot_data = await bot_db.get_bot(bot_id)

            if not bot_data.settings or "auto_reduce" not in bot_data.settings:
                button_data = False
            else:
                button_data = True

            # xlsx_path, photo_path = await stock_manager.export_xlsx(bot_id=bot_id)
            # json_path, photo_path = await stock_manager.export_json(bot_id=bot_id)
            # csv_path, photo_path = await stock_manager.export_csv(bot_id=bot_id)

            # media_group = MediaGroupBuilder()
            # media_group.add_document(media=FSInputFile(xlsx_path), caption="Excel таблица")
            # media_group.add_document(media=FSInputFile(json_path), caption="JSON файл")
            # media_group.add_document(media=FSInputFile(csv_path), caption="CSV таблица")

            # await bot.send_media_group(chat_id=query.message.chat.id, media=media_group.build())
            products = await product_db.get_all_products(bot_id)
            if len(products) == 0:
                await query.message.answer("Товаров на складе нет")
            else:
                await send_products_info_xlsx(bot_id, products)
            await query.message.answer(
                "Меню склада:",
                reply_markup=await InlineStockMenuKeyboard.get_keyboard(bot_id, button_data)
            )
            await query.answer()
        case callback_data.ActionEnum.BACK_TO_BOT_MENU:
            custom_bot = await bot_db.get_bot(bot_id)
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id)
            )


@stock_menu_router.callback_query(lambda query: InlineStockImportMenuKeyboard.callback_validator(query.data))
async def import_menu_handler(query: CallbackQuery, state: FSMContext):
    callback_data = InlineStockImportMenuKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id

    if callback_data.a == callback_data.ActionEnum.BACK_TO_STOCK_MENU:
        bot_data = await bot_db.get_bot(bot_id)

        if not bot_data.settings or "auto_reduce" not in bot_data.settings:
            auto_reduce = False
        else:
            auto_reduce = True

        return await query.message.edit_text(
            "Меню склада:",
            reply_markup=await InlineStockMenuKeyboard.get_keyboard(bot_id, auto_reduce),
            parse_mode=ParseMode.HTML
        )

    await query.message.edit_text(
        text=MessageTexts.STOCK_IMPORT_FILE_TYPE.value,
        reply_markup=InlineStockImportFileTypeKeyboard.get_keyboard(bot_id)
    )
    await state.set_data({"bot_id": bot_id, "action": callback_data.a.value})


@stock_menu_router.callback_query(lambda query: InlineStockImportFileTypeKeyboard.callback_validator(query.data))
async def pick_import_file_type(query: CallbackQuery, state: FSMContext):
    callback_data = InlineStockImportFileTypeKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id

    state_data = await state.get_data()

    try:
        action = state_data["action"]
    except KeyError:
        await query.answer("Вы уже импортировали товары", show_alert=True)
        await query.message.delete()
        return

    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_STOCK_MENU:
            return await query.message.edit_text(text=MessageTexts.STOCK_IMPORT_COMMANDS.value,
                                                 reply_markup=InlineStockImportMenuKeyboard.get_keyboard(bot_id),
                                                 parse_mode=ParseMode.HTML)
        case callback_data.ActionEnum.EXCEL:
            await query.message.delete()
            await query.message.answer(
                "Теперь отправьте боту xlsx / csv / json файл с товарами в таком же формате, "
                "как файлы из экспорта товаров.",
                reply_markup=ReplyBackStockMenuKeyboard.get_keyboard())
            await query.answer()
            await state.set_state(States.IMPORT_PRODUCTS)
            await state.set_data({"bot_id": bot_id, "file_type": callback_data.a.value, "action": action})
            return


@stock_menu_router.message(States.GOODS_COUNT_MANAGE)
async def handle_stock_manage_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if message.text == ReplyBackStockMenuKeyboard.Callback.ActionEnum.BACK_TO_STOCK_MENU.value:
        await message.edit_reply_markup(InlineStockImportFileTypeKeyboard.get_keyboard(state_data["bot_id"]))
        await state.set_state(States.BOT_MENU)
        await state.set_data({"action": state_data["action"], "bot_id": state_data["bot_id"]})
        return

    if message.content_type != "document":
        return await message.answer("Необходимо отправить xlsx файл с товарами.",
                                    reply_markup=ReplyBackStockMenuKeyboard.get_keyboard())
    file_extension = message.document.file_name.split('.')[-1].lower()
    if file_extension not in ("xlsx",):
        return await message.answer("Файл должен быть в формате xlsx товарами.",
                                    reply_markup=ReplyBackStockMenuKeyboard.get_keyboard())
    try:
        bot_id = (await state.get_data())['bot_id']
        file_path = f"{FILES_PATH}docs/{datetime.now().strftime('%d$m%Y_%H%M%S')}.{file_extension}"
        await bot.download(message.document.file_id, destination=file_path)
        await stock_manager.import_xlsx(bot_id=bot_id, path_to_file=file_path, replace=False)
        await message.answer("Кол-во товаров на складе обновлено.")
    except Exception as e:
        # TODO
        logger.error(
            f"user_id={message.from_user.id}: TODO exception is not dispatched",
            extra=extra_params(user_id=message.from_user.id),
            exc_info=e
        )
        raise e


@stock_menu_router.message(States.IMPORT_PRODUCTS)
async def handle_stock_import_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if message.text == ReplyBackStockMenuKeyboard.Callback.ActionEnum.BACK_TO_STOCK_MENU.value:

        await message.answer(
            text=MessageTexts.STOCK_IMPORT_FILE_TYPE.value,
            reply_markup=InlineStockImportFileTypeKeyboard.get_keyboard(bot_id=state_data['bot_id'])
        )
        await state.set_state(States.BOT_MENU)
        await state.set_data({"action": state_data["action"], "bot_id": state_data["bot_id"]})
        return

    if message.content_type != "document":
        return await message.answer("Необходимо отправить файл с товарами.",
                                    reply_markup=ReplyBackStockMenuKeyboard.get_keyboard())
    file_extension = message.document.file_name.split('.')[-1].lower()
    print(state_data["file_type"])
    match state_data["file_type"]:
        case InlineStockImportFileTypeKeyboard.Callback.ActionEnum.EXCEL.value:
            if file_extension not in ("xlsx",):
                return await message.answer("Файл должен быть в формате xlsx",
                                            reply_markup=ReplyBackStockMenuKeyboard.get_keyboard())

    # if file_extension not in ("xlsx", "json", "csv"):
    #     return await message.answer("Файл должен быть в формате xlsx / json / csv",
    #                                 reply_markup=ReplyBackStockMenuKeyboard.get_keyboard())
    try:
        bot_id = state_data['bot_id']
        file_path = f"{FILES_PATH}docs/{datetime.now().strftime('%d$m%Y_%H%M%S')}.{file_extension}"
        await bot.download(message.document.file_id, destination=file_path)
        if state_data['action'] == "replace_all":
            replace = True
        else:
            replace = False
        if state_data['action'] == "replace_duplicates":
            replace_d = True
        else:
            replace_d = False
        match file_extension:
            case "xlsx":
                await stock_manager.import_xlsx(bot_id=bot_id, path_to_file=file_path, replace=replace,
                                                replace_duplicates=replace_d)
            case "json":
                await stock_manager.import_json(bot_id=bot_id, path_to_file=file_path, replace=replace,
                                                replace_duplicates=replace_d)
            case "csv":
                await stock_manager.import_csv(bot_id=bot_id, path_to_file=file_path, replace=replace,
                                               replace_duplicates=replace_d)
        await message.answer("Товары обновлены.")
        await _back_to_stock_menu(message, state)
    except Exception as e:
        # TODO
        logger.error(
            f"user_id={message.from_user.id}: TODO exception is not dispatched",
            extra=extra_params(user_id=message.from_user.id),
            exc_info=e
        )
        raise e


async def _back_to_stock_menu(message: Message, state: FSMContext) -> None:
    bot_id = (await state.get_data())['bot_id']
    bot_data = await bot_db.get_bot(bot_id)

    if not bot_data.settings or "auto_reduce" not in bot_data.settings:
        auto_reduce = False
    else:
        auto_reduce = True

    await message.answer(
        "Возвращаемся в меню склада...",
        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id)
    )
    await message.answer(
        "Меню склада:",
        reply_markup=await InlineStockMenuKeyboard.get_keyboard(bot_id, auto_reduce)
    )
    await state.set_state(States.BOT_MENU)
    await state.set_data({'bot_id': bot_id})
