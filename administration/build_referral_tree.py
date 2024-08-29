import asyncio

from aiogram import Bot

from common_utils.config import main_telegram_bot_settings

from database.models.models import Database
from database.models.referral_invite_model import ReferralInviteDao

from logs.config import db_logger


database: Database = Database(
    sqlalchemy_url="",
    logger=db_logger,
    unique_id="util",
)
referral_invite_db: ReferralInviteDao = database.get_referral_invite_dao()


async def main() -> None:
    bot = Bot(main_telegram_bot_settings.TELEGRAM_TOKEN)
    cache = {}

    all_invites = await referral_invite_db.get_all_invites()
    chains = []
    for ind, invite in enumerate(all_invites, start=1):
        chain = [invite.user_id]
        if invite.came_from:
            temp_invite = invite.model_copy()
            while temp_invite.came_from:
                came_from = temp_invite.came_from
                chain.append(came_from)
                temp_invite = await referral_invite_db.get_invite_by_user_id(came_from)
            chains.append(" -> ".join([await _convert_id_to_username(bot, cache, x) for x in chain[::-1]]))

        print(f"{ind}/{len(all_invites)}: invite has been handled")

    print(*chains, sep="\n")


async def _convert_id_to_username(bot: Bot, cache: dict, user_id: int) -> str:
    if user_id in cache:
        return cache[user_id]

    chat = await bot.get_chat(chat_id=user_id)
    if chat.username:
        username = "@" + chat.username
    else:
        username = str(user_id)

    cache[user_id] = username
    return username


if __name__ == "__main__":
    asyncio.run(main())
