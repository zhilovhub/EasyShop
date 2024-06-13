from bot.handlers.routers import stock_menu_router
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder
from bot.states import States
from bot.keyboards import *
from bot.main import stock_manager, bot, bot_db
from config import FILES_PATH
from datetime import datetime


@stock_menu_router.message(lambda m: m.text and m.text == STOCK_STATE_BACK_BUTTON)
async def back_to_menu(message: Message, state: FSMContext):
    bot_id = (await state.get_data())['bot_id']
    await state.set_state(States.BOT_MENU)
    user_bot_db = await bot_db.get_bot(bot_id)
    user_bot = Bot(user_bot_db.token)
    user_bot_data = await user_bot.get_me()
    msg = await message.answer("Возвращаюсь в меню...", reply_markup=get_reply_bot_menu_keyboard(bot_id))
    # await msg.delete()
    await message.answer(
        MessageTexts.BOT_MENU_MESSAGE.value.format(user_bot_data.username),
        reply_markup=await get_inline_bot_menu_keyboard(bot_id)
    )
    await state.set_state(States.BOT_MENU)
    await state.set_data({'bot_id': bot_id})


@stock_menu_router.callback_query(lambda q: q.data.startswith("stock_menu:import"))
async def import_products_callback(query: CallbackQuery, state: FSMContext):
    bot_id = (await state.get_data())['bot_id']
    await query.message.answer(MessageTexts.STOCK_IMPORT_COMMANDS.value,
                               reply_markup=get_stock_import_options_keyboard(bot_id))



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
    file_extension = message.document.file_name.split('.')[-1].lower()
    if file_extension not in ("xlsx", ):
        return await message.answer("Файл должен быть в формате xlsx товарами.",
                                    reply_markup=get_stock_back_keyboard())
    try:
        bot_id = (await state.get_data())['bot_id']
        file_path = f"{FILES_PATH}docs/{datetime.now().strftime('%d$m%Y_%H%M%S')}.{file_extension}"
        await bot.download(message.document.file_id, destination=file_path)
        await stock_manager.import_xlsx(bot_id=bot_id, path_to_file=file_path, replace=False)
        await message.answer("Кол-во товаров на складе обновлено.")
    except:
        # TODO
        raise
