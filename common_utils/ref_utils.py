from aiogram import Bot
from aiogram.types import Message, FSInputFile
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.deep_linking import create_start_link

from bot.main import cache_resources_file_id_store
from bot.utils import MessageTexts
from bot.keyboards.start_keyboards import RefLinkKeyboard

from database.config import user_db, referral_invite_db
from database.models.user_model import UserStatusValues
from database.models.referral_invite_model import ReferralInviteNotFoundError, ReferralInviteSchemaWithoutId

from common_utils.config import common_settings

from logs.config import logger


async def handle_ref_user(user_id: int, bot: Bot) -> str:
    """
    Handles a referral user by creating a unique referral link and updating the database accordingly.

    If the user already has a referral link, it is retrieved from the database.
    Otherwise, a new link is created and stored in the database.

    Args:
        user_id (int): The ID of the user to handle.
        bot (Bot): The bot instance to use for creating the referral link.

    Returns:
        str: The referral link for the user.
    """
    ref_link = await create_start_link(bot, f"ref_{user_id}")
    try:
        invite = await referral_invite_db.get_invite_by_user_id(user_id)
        if invite.referral_deep_link is None:
            invite.referral_deep_link = ref_link
            await referral_invite_db.update_invite(invite)
        else:
            ref_link = invite.referral_deep_link

    except ReferralInviteNotFoundError:
        user = await user_db.get_user(user_id=user_id)
        await referral_invite_db.add_invite(
            ReferralInviteSchemaWithoutId(
                user_id=user_id,
                referral_deep_link=ref_link,
                paid=user.status == UserStatusValues.SUBSCRIBED,
            )
        )
    return ref_link


async def send_ref_user_info(message: Message, user_id: int, bot: Bot) -> None:
    file_ids = cache_resources_file_id_store.get_data()
    file_name = "ezshop_kp.pdf"
    ref_link = await handle_ref_user(user_id, bot)

    await message.answer(**MessageTexts.generate_ref_system_text(ref_link), reply_markup=RefLinkKeyboard.get_keyboard())

    try:
        await message.delete()
        await message.answer_document(
            document=file_ids[file_name],
        )
    except (TelegramBadRequest, KeyError) as e:
        logger.info(f"error while sending KP file.... cache is empty, sending raw files {e}")
        kp_message = await message.answer_document(
            document=FSInputFile(common_settings.RESOURCES_PATH.format(file_name)),
        )
        file_ids[file_name] = kp_message.document.file_id
        cache_resources_file_id_store.update_data(file_ids)
