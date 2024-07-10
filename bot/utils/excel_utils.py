from typing import List

from openpyxl import Workbook

from io import BytesIO

from bot.main import bot_db, contest_db
from bot.exceptions.exceptions import BotNotFound

from logs.config import logger, extra_params

from custom_bots.multibot import main_bot

from aiogram import Bot
from aiogram.types import BufferedInputFile

from database.models.contest_model import ContestUserSchema, ContestNotFound


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
        bot = await bot_db.get_bot(bot_id=contest.bot_id)
        created_by = bot.created_by
    except ContestNotFound:
        logger.error(f"Provided to excel function contest not found contest_id={contest_id}",
                     extra_params(contest_id=contest_id))
        return
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
