from aiogram.types import WebAppInfo

from common_utils.config import custom_telegram_bot_settings


def make_admin_panel_webapp_info(bot_id: int) -> WebAppInfo:
    return WebAppInfo(
        url=f"{custom_telegram_bot_settings.WEB_APP_URL}:{custom_telegram_bot_settings.WEB_APP_PORT}"
        f"{str(custom_telegram_bot_settings.WEB_APP_PORT)[-1]}"
        f"/admin-panel/?bot_id={bot_id}"
    )
