from bot.handlers.routers import stock_menu_router
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder
from bot.states import States
from bot.keyboards import *
from bot.main import stock_manager, bot


@stock_menu_router.callback_query(lambda q: q.data.startswith("stock_menu:import"))
async def import_products_callback(query: CallbackQuery, state: FSMContext):
    bot_id = query.data.split(':')[2]


@stock_menu_router.callback_query(lambda q: q.data.startswith("stock_menu:export"))
async def export_products_callback(query: CallbackQuery, state: FSMContext):
    bot_id = query.data.split(':')[2]
    xlsx_path, photo_path = await stock_manager.export_xlsx(bot_id=bot_id)
    json_path, photo_path = await stock_manager.export_json(bot_id=bot_id)
    csv_path, photo_path = await stock_manager.export_csv(bot_id=bot_id)
    media_group = MediaGroupBuilder()
    media_group.add_document(media=FSInputFile(xlsx_path), caption="Excel таблица")
    media_group.add_document(media=FSInputFile(json_path), caption="JSON файл")
    media_group.add_document(media=FSInputFile(csv_path), caption="CSV таблица")
    await bot.send_media_group(chat_id=query.message.chat.id, media=media_group.build())


@stock_menu_router.message(States.STOCK_MANAGE)
async def handle_stock_manage_input(message: Message, state: FSMContext):
    if message.content_type != "document":
        return await message.answer("Необходимо отправить xlsx файл с товарами.",
                                    reply_markup=get_stock_back_keyboard())
    if message.document.file_name.split('.')[-1].lower() != "xlsx":
        return await message.answer("Файл должен быть в формате xlsx товарами.",
                                    reply_markup=get_stock_back_keyboard())
    try:
        await stock_manager.import_xlsx(path_to_file="", replace=False)
    except:
        pass
