import asyncio

from aiogram import Bot
from aiogram.types import Message

from bot.main import subscription
from bot.utils import MessageTexts
from bot.keyboards.start_keyboards import ShortDescriptionKeyboard
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard

from common_utils.tests_utils import messages_collector
from common_utils.keyboards.remove_keyboard import OurReplyKeyboardRemove


# test
@messages_collector()
async def greetings_message(
    bot: Bot, custom_bot_id: int | None, message: Message, chat_id: int | None = None, is_first_message: bool = False
):
    chat_id = message.chat.id if not chat_id else chat_id
    from_chat_id = -1002218211760

    yield await bot.forward_message(  # Добро пожаловать
        chat_id=chat_id, from_chat_id=from_chat_id, message_id=4
    )
    await asyncio.sleep(5)

    yield await bot.forward_message(  # Краткий рассказ о продукте
        chat_id=chat_id, from_chat_id=from_chat_id, message_id=6
    )
    yield await message.answer(
        **MessageTexts.generate_menu_start_text(), reply_markup=ShortDescriptionKeyboard.get_keyboard()
    )

    if await subscription.is_user_subscribed(user_id=chat_id):
        if custom_bot_id:
            yield await bot.send_message(
                chat_id=chat_id,
                text=MessageTexts.ALREADY_HAS_BOT.value,
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(),
            )
        elif not is_first_message:  # Присылаем, что у пользователя нет бота, только если это не первое сообщение боту
            yield await bot.send_message(
                chat_id=chat_id, text=MessageTexts.HAS_NO_BOT_YET.value, reply_markup=OurReplyKeyboardRemove()
            )


# async def send_instructions(
#     bot: Bot, custom_bot_id: int | None, chat_id: int, cache_resources_file_id_store: JsonStore  # noqa
# ) -> None:
#     """Sends instruction and considers whether user has bots or not. Usually is called from /start"""

# file_ids = cache_resources_file_id_store.get_data()
# file_name = "start_instruction.png"
#
# bot_father_keyboard = InstructionKeyboard.get_keyboard()

# try:
#     await bot.send_photo(
#         chat_id=chat_id,
#         photo=file_ids[file_name],
#         caption=MessageTexts.INSTRUCTION_MESSAGE.value,
#         reply_markup=bot_father_keyboard,
#     )
#     if custom_bot_id:
#         await bot.send_message(
#             chat_id=chat_id, text="✅ У Вас уже есть бот", reply_markup=ReplyBotMenuKeyboard.get_keyboard()
#         )
#     else:
#         await bot.send_message(
#             chat_id=chat_id, text="❌ Вы всё ещё не создали бота", reply_markup=OurReplyKeyboardRemove()
#         )
# except (TelegramBadRequest, KeyError) as e:
#     logger.info(f"error while sending instructions.... cache is empty, sending raw files {e}")
#     instruction_message = await bot.send_photo(
#         chat_id=chat_id,
#         photo=FSInputFile(common_settings.RESOURCES_PATH.format(file_name)),
#         caption=MessageTexts.INSTRUCTION_MESSAGE.value,
#         reply_markup=bot_father_keyboard,
#     )
#     file_ids[file_name] = instruction_message.photo[-1].file_id
#     cache_resources_file_id_store.update_data(file_ids)
