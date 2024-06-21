from aiogram.types import BufferedInputFile
from aiogram.types import InputFile
from typing import List
from bot.exceptions.exceptions import BotNotFound
from database.models.contest_channel_model import ContestChannelSchema
from database.models.contest_user_model import ContestUser
from bot.main import channel_post_db, contest_user_db, contest_channel_db, bot_db, custom_bot_user_db
import random
from database.models.channel_post_model import ContestTypeValues
from custom_bots.multibot import main_bot
from aiogram.types.chat_member import ChatMember
from aiogram.types.chat_member_member import ChatMemberMember
import openpyxl
from openpyxl import Workbook
from io import BytesIO


def create_excel(data, sheet_name):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Добавляем заголовки
    headers = ["user_id", "username", "join_date"]
    ws.append(headers)

    # Добавляем данные
    for user in data:
        ws.append([user["user_id"], user["username"], user["join_date"]])

    return wb


async def generate_contest_result(channel_id: int):
    channel_post = await channel_post_db.get_channel_post(channel_id, is_contest=True)
    users = await contest_user_db.get_contest_users_by_contest_id(channel_post.channel_post_id)
    channels = await contest_channel_db.get_contest_channels_by_contest_post_id(channel_post.channel_post_id)
    users_copy = users.copy()
    winners_list: List[ContestUser] = []
    bot_id = channel_post.bot_id
    try:
        bot = await bot_db.get_bot(bot_id=bot_id)
        created_by = bot.created_by
    except BotNotFound:
        return
    if channel_post.contest_type == ContestTypeValues.RANDOM:
        winners_amount = channel_post.contest_winner_amount
        while len(users_copy) != 0:
            if len(winners_list) >= winners_amount:
                break
            random_user = random.choice(users_copy)
            winners_list.append(random_user)
            users_copy.remove(random_user)
    else:
        winners_amount = channel_post.contest_winner_amount
        while len(users_copy) != 0:
            if len(winners_list) >= winners_amount:
                break
            random_user = random.choice(users_copy)
            for channel in channels:
                try:
                    status = await main_bot.get_chat_member(channel.channel_id, random_user.user_id)
                except Exception:
                    continue
                if status == ChatMemberMember:
                    winners_list.append(random_user)
                    users_copy.remove(random_user)
    wb_data = []
    for user in winners_list:
        chat = await main_bot.get_chat(user.user_id)
        username = chat.username
        wb_data.append(
            {"user_id": user.user_id, "username": username,
             "join_date": str(user.join_date)}
        )
    winners_wb = create_excel(wb_data, "Winners")
    winners_buffer = BytesIO()
    winners_wb.save(winners_buffer)
    winners_buffer.seek(0)
    winners_file = BufferedInputFile(
        winners_buffer.read(), filename="winners.xlsx")
    await main_bot.send_document(created_by, document=winners_file,
                                 caption='winners.xlsx')
    winners_buffer.close()
    await channel_post_db.delete_channel_post(channel_post.channel_post_id)
    # if channel_post.contest_type == ContestTypeValues.SPONSOR:
    #     await contest_channel_db.delete_channels_by_contest_id(channel_post.channel_post_id)
