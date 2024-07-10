from typing import List

from openpyxl import Workbook

from io import BytesIO

from bot.main import bot_db, contest_db
from bot.exceptions.exceptions import BotNotFound

from custom_bots.multibot import main_bot

from aiogram import Bot
from aiogram.types import BufferedInputFile

from database.models.contest_model import ContestUserSchema


def create_excel(data, sheet_name, table_type):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Добавляем заголовки
    match table_type:
        case "banned":
            headers = ["user_id", "username"]
        case "contest":
            headers = ["user_id", "username", "full_name", "took part time", "won"]
        case _:
            headers = ["user_id", "username"]
    ws.append(headers)

    # Добавляем данные
    for user in data:
        ws.append([user[header] for header in headers])

    return wb


async def send_ban_users_xlsx(users_list: List[int], bot_id: int):
    try:
        bot = await bot_db.get_bot(bot_id=bot_id)
        created_by = bot.created_by
    except BotNotFound:
        return
    custom_bot = Bot(token=bot.token)
    wb_data = []
    for user in users_list:
        chat = await custom_bot.get_chat(user)
        username = chat.username
        wb_data.append(
            {"user_id": user, "username": username, }
        )
    ban_users_wb = create_excel(wb_data, "Banned", "banned")
    ban_users_buffer = BytesIO()
    ban_users_wb.save(ban_users_buffer)
    ban_users_buffer.seek(0)
    ban_users_file = BufferedInputFile(
        ban_users_buffer.read(), filename="ban_users.xlsx")
    await main_bot.send_document(created_by, document=ban_users_file,
                                 caption="ban_users.xlsx")
    ban_users_buffer.close()


async def send_contest_results_xlsx(users: list[ContestUserSchema], contest_id: int):
    try:
        contest = await contest_db.get_contest_by_contest_id(contest_id)
        bot = await bot_db.get_bot(bot_id=contest.bot_id)
        created_by = bot.created_by
    except BotNotFound:
        return

    wb_data = []
    for user in users:
        wb_data.append(
            {"user_id": user.user_id, "username": "@" + str(user.username), "full_name": user.full_name,
             "took part time": user.join_date, "won": user.is_won}
        )
    contest_users_wb = create_excel(wb_data, "Contest", "contest")
    contest_users_buffer = BytesIO()
    contest_users_wb.save(contest_users_buffer)
    contest_users_buffer.seek(0)
    contest_users_file = BufferedInputFile(
        contest_users_buffer.read(), filename="contest_users.xlsx")
    await main_bot.send_document(created_by, document=contest_users_file,
                                 caption="Список участников конкурса.")
    contest_users_buffer.close()
