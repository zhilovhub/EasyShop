from aiogram.enums import ParseMode

from bot.handlers.routers import stock_menu_router
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder
from bot.states import States
from bot.keyboards import *
from bot.keyboards.main_menu_keyboards import InlineBotMenuKeyboard, ReplyBotMenuKeyboard
from bot.keyboards.stock_menu_keyboards import InlineStockMenuKeyboard, ReplyBackStockMenuKeyboard
from bot.main import stock_manager, bot, bot_db, product_db
from bot.config import FILES_PATH
from datetime import datetime


@stock_menu_router.callback_query(lambda query: InlineStockMenuKeyboard.callback_validator(query.data))
async def stock_menu_handler(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    callback_data = InlineStockMenuKeyboard.Callback.model_validate_json(query.data)

    bot_id = callback_data.bot_id

    match callback_data.a:
        case "channels":  # TODO should not be here
            custom_bot = await bot_db.get_bot(state_data["bot_id"])
            await query.message.edit_text(
                MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await get_inline_bot_channels_list_keyboard(custom_bot.bot_id)
            )

        case "channel":  # TODO should not be here
            custom_bot = await bot_db.get_bot(state_data["bot_id"])
            custom_tg_bot = Bot(custom_bot.token)
            channel_id = int(query.data.split(":")[-1])
            channel_username = (await custom_tg_bot.get_chat(channel_id)).username
            await query.message.edit_text(
                MessageTexts.BOT_CHANNEL_MENU_MESSAGE.value.format(channel_username,
                                                                   (await custom_tg_bot.get_me()).username),
                reply_markup=await get_inline_channel_menu_keyboard(custom_bot.bot_id, int(query.data.split(":")[-1]))
            )

        case callback_data.ActionEnum.GOODS_COUNT:
            products = await product_db.get_all_products(bot_id)
            await query.message.answer(f"Количество товаров: {len(products)}")
            await query.answer()
            # case "goods_list":
            #     products = await product_db.get_all_products(state_data["bot_id"])
            #     if not products:
            #         await query.message.answer("Список товаров Вашего магазина пуст")
            #     else:
            #         await query.message.answer(
            #             "Список товаров Вашего магазина 👇\nЧтобы удалить товар, нажмите на тег рядом с ним")
            #         for product in products:
            #             await query.message.answer_photo(
            #                 photo=FSInputFile(os.getenv('FILES_PATH') + product.picture),
            #                 caption=f"<b>{product.name}</b>\n\n"
            #                         f"Цена: <b>{float(product.price)}₽</b>",
            #                 reply_markup=get_inline_delete_button(product.id))
            #     await query.answer()
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
            except:
                # handle telegram api error "message not modified"
                pass
        case callback_data.ActionEnum.IMPORT:
            await query.message.answer(
                MessageTexts.STOCK_IMPORT_COMMANDS.value,
                reply_markup=get_stock_import_options_keyboard(bot_id)
            )
        case callback_data.ActionEnum.EXPORT:
            bot_data = await bot_db.get_bot(bot_id)

            if not bot_data.settings or "auto_reduce" not in bot_data.settings:
                button_data = False
            else:
                button_data = True

            xlsx_path, photo_path = await stock_manager.export_xlsx(bot_id=bot_id)
            json_path, photo_path = await stock_manager.export_json(bot_id=bot_id)
            csv_path, photo_path = await stock_manager.export_csv(bot_id=bot_id)

            media_group = MediaGroupBuilder()
            media_group.add_document(media=FSInputFile(xlsx_path), caption="Excel таблица")
            media_group.add_document(media=FSInputFile(json_path), caption="JSON файл")
            media_group.add_document(media=FSInputFile(csv_path), caption="CSV таблица")

            await bot.send_media_group(chat_id=query.message.chat.id, media=media_group.build())
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


@stock_menu_router.callback_query(lambda q: q.data.startswith("import_menu:"))
async def import_menu_handler(query: CallbackQuery, state: FSMContext):
    bot_id = query.data.split(':')[2]
    action = query.data.split(':')[1]
    await state.set_state(States.IMPORT_PRODUCTS)
    await state.set_data({"bot_id": bot_id, "action": action})
    await query.message.answer("Теперь отправьте боту xlsx / csv / json файл с товарами в таком же формате, "
                               "как файлы из экспорта товаров.", reply_markup=ReplyBackStockMenuKeyboard.get_keyboard())


@stock_menu_router.message(States.GOODS_COUNT_MANAGE)
async def handle_stock_manage_input(message: Message, state: FSMContext):
    if message.text == ReplyBackStockMenuKeyboard.Callback.ActionEnum.BACK_TO_STOCK_MENU.value:
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
    except:
        # TODO
        raise


@stock_menu_router.message(States.IMPORT_PRODUCTS)
async def handle_stock_import_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if message.content_type != "document":
        return await message.answer("Необходимо отправить файл с товарами.",
                                    reply_markup=ReplyBackStockMenuKeyboard.get_keyboard())
    file_extension = message.document.file_name.split('.')[-1].lower()
    if file_extension not in ("xlsx", "json", "csv"):
        return await message.answer("Файл должен быть в формате xlsx / json / csv",
                                    reply_markup=ReplyBackStockMenuKeyboard.get_keyboard())
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
    except:
        # TODO
        raise
