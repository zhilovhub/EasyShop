from .env_config import (
    Settings,
    APISettings,
    LogsSettings,
    CommonSettings,
    DatabaseSettings,
    CryptographySettings,
    MainTelegramBotSettings,
    CustomTelegramBotSettings,
    TechSupportBotSettings,
)

settings = Settings()
api_settings = APISettings()
logs_settings = LogsSettings()
common_settings = CommonSettings()
database_settings = DatabaseSettings()
cryptography_settings = CryptographySettings()
main_telegram_bot_settings = MainTelegramBotSettings()
custom_telegram_bot_settings = CustomTelegramBotSettings()
tech_support_settings = TechSupportBotSettings()
