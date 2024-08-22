from aiogram.types import Message, FSInputFile
from aiogram.filters import Command, CommandObject

from bot.main import MAINTENANCE, START_MESSAGE_ANALYTICS
from bot.handlers.routers import admin_group_commands_router

from logs.config import logger


def _get_maintenance_data() -> dict:
    """
    :return: Maintenance options of the main bot
    """
    json_data = MAINTENANCE.get_data()
    if not json_data:
        json_data = {"maintenance": {"maintenance_status": False, "maintenance_reason": None}}
        logger.info(f"maintenance json data is empty, setting new default data {json_data}")
        MAINTENANCE.update_data(json_data)
    return json_data["maintenance"]


@admin_group_commands_router.message(Command("ref_analytics"))
async def bot_ref_analytics_command_handler(message: Message) -> None:
    """Send the json analytics on referal start messages"""
    await message.answer_document(
        document=FSInputFile(START_MESSAGE_ANALYTICS.file_path),
    )


@admin_group_commands_router.message(Command("bot_status"))
async def bot_status_command_handler(message: Message) -> None:
    """Показывает, на тех обс"""

    data = _get_maintenance_data()
    text = "<b><i>Статус бота:</i></b>\n"
    if data["maintenance_status"]:
        text += "\n🟡 <b>Обслуживание в процессе.</b>\n"
        maintenance_text = (
            data["maintenance_reason"] if data["maintenance_reason"] else "🛠 Бот находится в режиме обслуживания."
        )
        text += f"\n<b>Текст для пользователей:</b>\n<pre>{maintenance_text}</pre>"
    else:
        text += "\n🟢 <b>Бот работает в обычном режиме.</b>"
    await message.answer(text)


@admin_group_commands_router.message(Command("on_maintenance"))
async def on_maintenance_command_handler(message: Message, command: CommandObject) -> None:
    data = _get_maintenance_data()
    if command.args is None:
        maintenance_text = None
        text = "✓ Обслуживание бота <b>включено</b> с <u>дефолтным</u> текстом для пользователей."
    else:
        maintenance_text = command.args
        text = "✓ Обслуживание бота <b>включено</b> с <u>указанным в сообщении</u> текстом для пользователей."
    data["maintenance_status"] = True
    data["maintenance_reason"] = maintenance_text
    MAINTENANCE.update_data({"maintenance": data})
    await message.reply(text)


@admin_group_commands_router.message(Command("off_maintenance"))
async def off_maintenance_command_handler(message: Message) -> None:
    data = _get_maintenance_data()
    if data["maintenance_status"]:
        data["maintenance_status"] = False
        data["maintenance_reason"] = None
        MAINTENANCE.update_data({"maintenance": data})
        await message.reply("✓ Обслуживание бота <b>выключено</b>")
    else:
        await message.reply("✗ Обслуживание итак <b>не было включено</b>.")
