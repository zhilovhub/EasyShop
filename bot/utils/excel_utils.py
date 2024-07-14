import os
from typing import List

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font
from openpyxl.styles.colors import Color

from io import BytesIO

from bot.main import bot_db, contest_db, category_db
from bot.exceptions.exceptions import BotNotFound

from logs.config import logger, extra_params

from custom_bots.multibot import main_bot

from aiogram import Bot
from aiogram.types import BufferedInputFile

from database.models.contest_model import ContestUserSchema, ContestNotFound
from database.models.product_model import ProductSchema
from zipfile import ZipFile


def create_zip_buffer(images) -> BufferedInputFile:
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, 'w') as zip_file:
        for file_path in images:
            file_name = os.path.basename(file_path)
            with open(file_path, 'rb') as file:
                zip_file.writestr(file_name, file.read())
    zip_buffer.seek(0)
    buffer_file = BufferedInputFile(zip_buffer.read(), filename="images.zip")
    return buffer_file


def _make_xlsx_buffer(name: str, wb_data) -> BufferedInputFile:
    wb = create_excel(wb_data, name, name)
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    buffer_file = BufferedInputFile(buffer.read(), filename=f"{name}.xlsx")
    buffer.close()
    return buffer_file


def create_excel(data, sheet_name, table_type):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Добавляем заголовки
    match table_type:
        case "banned":
            headers = ["user_id", "username"]
            ws.append(headers)

        case "contest":
            headers = ["user_id", "username", "full_name", "took part time", "won"]
            ws.append(headers)

        case "product_export":
            headers = ["id", "Имя", "Описание", "Цена", "Остаток", "Артикул", "Категория", "Картинки товара"]
            ws.append(headers)
            for product in data:
                ws.append([product[header] for header in headers])

            # header_fill = PatternFill(start_color="FFCCFFCC", end_color="FFCCFFCC", fill_type="solid")
            # even_fill = PatternFill(start_color="FFE6FFCC", end_color="FFE6FFCC", fill_type="solid")
            # odd_fill = PatternFill(start_color="FFFFF2CC", end_color="FFFFF2CC", fill_type="solid")
            header_fill = PatternFill(fgColor="FFCCFFCC", patternType="solid", fill_type="solid")
            even_fill = PatternFill(fgColor="FFE6FFCC", patternType="solid", fill_type="solid")
            odd_fill = PatternFill(fgColor="FFFFF2CC", patternType="solid", fill_type="solid")
            thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                 top=Side(style='thin'), bottom=Side(style='thin'))
            bold_font = Font(bold=True)
            alignment = Alignment(horizontal="center", vertical="center")
            for col in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = bold_font
                cell.alignment = alignment
                cell.border = thin_border

            # Применяем стили к остальным строкам
            for row in range(2, len(data) + 2):  # Начинаем с 2-й строки до последней строки данных
                for col in range(1, len(headers) + 1):
                    cell = ws.cell(row=row, column=col)
                    if row % 2 == 0:
                        cell.fill = even_fill
                    else:
                        cell.fill = odd_fill
                    cell.alignment = alignment
                    cell.border = thin_border

            # Устанавливаем ширину колонок
            for col in range(1, len(headers) + 1):
                max_length = 0
                column = get_column_letter(col)
                for cell in ws[column]:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column].width = adjusted_width
        case _:
            headers = ["user_id", "username"]
            ws.append(headers)

    # Добавляем данные
    if table_type != "product_export":
        for user in data:
            ws.append([user[header] for header in headers])

    return wb


async def send_ban_users_xlsx(users_list: List[int], bot_id: int):
    try:
        bot = await bot_db.get_bot(bot_id=bot_id)
        created_by = bot.created_by
    except BotNotFound:
        logger.error(f"Provided to excel function bot not found bot_id={bot_id}",
                     extra_params(bot_id=bot_id))
        return
    custom_bot = Bot(token=bot.token)
    wb_data = []
    for user in users_list:
        chat = await custom_bot.get_chat(user)
        username = chat.username
        wb_data.append(
            {"user_id": user, "username": username, }
        )
    buffered_file = _make_xlsx_buffer("banned", wb_data)
    await main_bot.send_document(created_by, document=buffered_file,
                                 caption="ban_users.xlsx")


async def send_contest_results_xlsx(users: list[ContestUserSchema], contest_id: int):
    try:
        contest = await contest_db.get_contest_by_contest_id(contest_id)
    except ContestNotFound:
        logger.error(f"Provided to excel function contest not found contest_id={contest_id}",
                     extra_params(contest_id=contest_id))
        return

    try:
        bot = await bot_db.get_bot(bot_id=contest.bot_id)
        created_by = bot.created_by
    except BotNotFound:
        logger.error(f"Provided to excel function bot not found bot_id={contest.bot_id}",
                     extra_params(bot_id=contest.bot_id))
        return

    wb_data = []
    for user in users:
        wb_data.append(
            {"user_id": user.user_id, "username": "@" + str(user.username), "full_name": user.full_name,
             "took part time": user.join_date, "won": user.is_won}
        )
    buffered_file = _make_xlsx_buffer("contest", wb_data)
    await main_bot.send_document(created_by, document=buffered_file,
                                 caption="Список участников конкурса.")


async def send_products_info_xlsx(products: list[ProductSchema]):
    wb_data = []
    files_path = os.environ["FILES_PATH"]
    images = []
    try:
        bot = await bot_db.get_bot(bot_id=products[0].bot_id)
        created_by = bot.created_by
    except BotNotFound:
        logger.error(f"Provided to excel function bot not found bot_id={products[0].bot_id}",
                     extra_params(bot_id=products[0].bot_id))
        return
    for product in products:
        categories = []
        if product.category:
            for cat in product.category:
                cat_obj = await category_db.get_category(cat)
                categories.append(cat_obj.name)
            categories_text = "/".join(categories)
        else:
            categories_text = "Категория не задана"

        if product.picture:
            images_text = "/".join(product.picture)
            images.extend([files_path + prod for prod in product.picture])
        else:
            images_text = "Картинки не найдены"
        wb_data.append(
            {"id": product.id, "Имя": product.name, "Описание": product.description,
             "Цена": product.price, "Остаток": product.count, "Артикул": product.article,
             "Категория": categories_text, "Картинки товара": images_text}
        )

    if len(images) != 0:
        buffered_zip_file = create_zip_buffer(images)
        await main_bot.send_document(created_by, document=buffered_zip_file, caption="Картинки ваших товаров")
    buffered_file = _make_xlsx_buffer("product_export", wb_data)
    await main_bot.send_document(created_by, document=buffered_file,
                                 caption="Список товаров загруженных в систему")
