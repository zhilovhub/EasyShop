import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from common_utils.storage import support_bot_storage
from common_utils.bot_settings_config import BOT_PROPERTIES
from common_utils.start_message import send_start_message_to_admins
from common_utils.config import tech_support_settings, common_settings, main_telegram_bot_settings

from logs.config import tech_support_logger


bot = Bot(tech_support_settings.TECH_SUPPORT_BOT_TOKEN, default=BOT_PROPERTIES)
dp = Dispatcher(storage=support_bot_storage)

main_bot = Bot(main_telegram_bot_settings.TELEGRAM_TOKEN, default=BOT_PROPERTIES)


async def on_start():
    tech_support_logger.info("onStart called")

    commands = [
        BotCommand(command="start", description="Открыть меню бота"),
        BotCommand(command="faq", description="Частые вопросы"),
    ]

    await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())

    await support_bot_storage.connect()

    tech_support_logger.info("onStart finished. Support Bot online")

    bot_data = await bot.get_me()

    await send_start_message_to_admins(
        bot=bot,
        admins=tech_support_settings.TECH_SUPPORT_ADMINS,
        msg_text=f"Support Bot started! (@{bot_data.username})",
    )
    await send_start_message_to_admins(
        bot=main_bot, admins=common_settings.TECH_ADMINS, msg_text=f"Support Bot started! (@{bot_data.username})"
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    from tech_support.handlers import admins_router, users_router

    dp.include_router(admins_router)
    dp.include_router(users_router)

    for log_file in ("all.log", "err.log"):
        with open(common_settings.LOGS_PATH + log_file, "a") as log:
            log.write(
                f"=============================\n"
                f"New bot-app session\n"
                f"[{datetime.now()}]\n"
                f"=============================\n"
            )
    asyncio.run(on_start())
