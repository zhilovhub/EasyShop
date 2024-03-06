from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, InputMediaPhoto

from bot import config
from bot.main import db_engine
from bot.utils import JsonStore
from bot.config import logger
from bot.keyboards import *
from bot.states.states import States
from bot.handlers.routers import commands_router
from bot.exceptions.exceptions import *
from database.models.user_model import UserSchema

cache_resources_file_id_store = JsonStore(
    file_path=config.RESOURCES_PATH.format("cache.json"),
    json_store_name="RESOURCES_FILE_ID_STORE"
)


@commands_router.message(CommandStart())
async def start_command_handler(message: Message, state: FSMContext):
    try:
        await db_engine.get_user_dao().get_user(message.from_user.id)
    except UserNotFound:
        logger.info(f"user {message.from_user.id} not found in db, creating new instance...")

        await db_engine.get_user_dao().add_user(UserSchema(
            user_id=message.from_user.id, registered_at=datetime.utcnow(), status="new", locale="default")
        )

    await message.answer(MessageTexts.ABOUT_MESSAGE.value)

    user_bots = await db_engine.get_bot_dao().get_bots(message.from_user.id)
    if not user_bots:
        await state.set_state(States.WAITING_FOR_TOKEN)

        file_ids = cache_resources_file_id_store.get_data()
        try:
            await message.answer_media_group(
                media=[
                    InputMediaPhoto(media=file_ids["botFather1.jpg"], caption=MessageTexts.INSTRUCTION_MESSAGE.value),
                    InputMediaPhoto(media=file_ids["botFather2.jpg"]),
                    InputMediaPhoto(media=file_ids["botFather3.jpg"])
                ]
            )
        except (TelegramBadRequest, KeyError) as e:
            logger.info(f"error while sending instructions.... cache is empty, sending raw files {e}")
            media_group = await message.answer_media_group(
                media=[
                    InputMediaPhoto(media=FSInputFile(config.RESOURCES_PATH.format("botFather1.jpg")), caption=MessageTexts.INSTRUCTION_MESSAGE.value),
                    InputMediaPhoto(media=FSInputFile(config.RESOURCES_PATH.format("botFather2.jpg"))),
                    InputMediaPhoto(media=FSInputFile(config.RESOURCES_PATH.format("botFather3.jpg"))),
                ]
            )
            for ind, message in enumerate(media_group, start=1):
                file_ids[f"botFather{ind}.jpg"] = message.photo[0].file_id
            cache_resources_file_id_store.update_data(file_ids)
    else:
        bot_id = user_bots[0].bot_id
        user_bot = Bot(user_bots[0].token)
        user_bot_data = await user_bot.get_me()
        await message.answer(MessageTexts.BOT_SELECTED_MESSAGE.value.replace(
            "{selected_name}", user_bot_data.full_name
        ),
            reply_markup=get_bot_menu_keyboard(bot_id=bot_id))
        await state.set_state(States.BOT_MENU)
        await state.set_data({'bot_id': bot_id})
