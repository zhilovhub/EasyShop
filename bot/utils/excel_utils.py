from typing import List

import openpyxl
from openpyxl import Workbook

from io import BytesIO

from bot.main import custom_bot_user_db, bot_db
from bot.exceptions.exceptions import BotNotFound

from database.models.custom_bot_user_model import CustomBotUser

from custom_bots.multibot import main_bot

from aiogram.types import BufferedInputFile


def create_excel(data, sheet_name):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Добавляем заголовки
    headers = ["user_id", "username"]
    ws.append(headers)

    # Добавляем данные
    for user in data:
        ws.append([user["user_id"], user["username"]])

    return wb


async def send_ban_users_xlsx(users_list: List[int], bot_id: int):
    try:
        bot = await bot_db.get_bot(bot_id=bot_id)
        created_by = bot.created_by
    except BotNotFound:
        return
    wb_data = []
    for user in users_list:
        chat = await main_bot.get_chat(user)
        username = chat.username
        wb_data.append(
            {"user_id": user, "username": username, }
        )
    ban_users_wb = create_excel(wb_data, "Banned")
    ban_users_buffer = BytesIO()
    ban_users_wb.save(ban_users_buffer)
    ban_users_buffer.seek(0)
    ban_users_file = BufferedInputFile(
        ban_users_buffer.read(), filename="ban_users.xlsx")
    await main_bot.send_document(created_by, document=ban_users_file,
                                 caption='ban_users.xlsx')
    ban_users_buffer.close()
