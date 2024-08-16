from aiogram.utils.deep_linking import create_start_link
from database.config import user_db, referral_invite_db
from aiogram import Bot
from database.models.referral_invite_model import ReferralInviteNotFoundError, ReferralInviteSchemaWithoutId
from database.models.user_model import UserStatusValues


async def _handle_ref_user(user_id: int, bot: Bot) -> str:
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
