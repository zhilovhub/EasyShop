from .env_config import (
    Settings,
    APISettings,
    LogsSettings,
    CommonSettings,
    DatabaseSettings,
    MainTelegramBotSettings,
    CustomTelegramBotSettings
)

settings = Settings()
api_settings = APISettings()
logs_settings = LogsSettings()
common_settings = CommonSettings()
database_settings = DatabaseSettings()
main_telegram_bot_settings = MainTelegramBotSettings()
custom_telegram_bot_settings = CustomTelegramBotSettings()
