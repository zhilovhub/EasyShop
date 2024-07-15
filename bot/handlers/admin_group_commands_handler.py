from aiogram import F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from bot.main import MAINTENANCE
from bot.handlers.routers import admin_group_commands_router

from logs.config import logger


def _get_maintenance_data() -> dict:
    json_data = MAINTENANCE.get_data()
    if not json_data:
        json_data = {
            "maintenance":
                {
                    "maintenance_status": False,
                    "maintenance_reason": None
                }
        }
        logger.info(f"maintenance json data is empty, setting new default data {json_data}")
        MAINTENANCE.update_data(json_data)
    return json_data['maintenance']


@admin_group_commands_router.message(F.text == "/bot_status")
async def bot_status_command_handler(message: Message, state: FSMContext) -> None:
    data = _get_maintenance_data()
    text = "<b><i>Статус бота:</i></b>\n"
    if data['maintenance_status']:
        text += "\n🟡 <b>Обслуживание в процессе.</b>\n"
        maintenance_text = data['maintenance_reason'] if data['maintenance_reason'] else "🛠 Бот находится в режиме обслуживания."
        text += f"\n<b>Текст для пользователей:</b>\n<pre>{maintenance_text}</pre>"
    else:
        text += "\n🟢 <b>Бот работает в обычном режиме.</b>"
    await message.answer(text)


@admin_group_commands_router.message(lambda m: m.text.startswith("/on_maintenance"))
async def on_maintenance_command_handler(message: Message, state: FSMContext) -> None:
    data = _get_maintenance_data()
    params = message.text.strip().split(maxsplit=1)
    if len(params) == 1:
        maintenance_text = None
        text = "✓ Обслуживание бота <b>включено</b> с <u>дефолтным</u> текстом для пользователей."
    else:
        maintenance_text = params[1]
        text = "✓ Обслуживание бота <b>включено</b> с <u>указанным в сообщении</u> текстом для пользователей."
    data['maintenance_status'] = True
    data['maintenance_reason'] = maintenance_text
    MAINTENANCE.update_data({"maintenance": data})
    await message.reply(text)


@admin_group_commands_router.message(F.text == "/off_maintenance")
async def off_maintenance_command_handler(message: Message, state: FSMContext) -> None:
    data = _get_maintenance_data()
    if data['maintenance_status']:
        data['maintenance_status'] = False
        data['maintenance_reason'] = None
        MAINTENANCE.update_data({"maintenance": data})
        await message.reply("✓ Обслуживание бота <b>выключено</b>")
    else:
        await message.reply("✗ Обслуживание итак <b>не было включено</b>.")
