from enum import Enum
from dotenv import find_dotenv

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Mode(Enum):
    PROD = "PROD"
    TEXT = "TEST"


class Settings(BaseSettings):
    """Base Settings class for other Settings"""

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=find_dotenv("../../.env", raise_error_if_not_found=True),
    )

    MODE: Mode  # TEST or PROD


class APISettings(Settings):
    """API settings"""

    API_PROTOCOL: str
    API_HOST: str
    API_PORT: int

    SSL_KEY_PATH: str | None = None
    SSL_CERT_PATH: str | None = None

    API_DEBUG_MODE: bool

    UDS_PATH: str
    DEVELOPERS: list[tuple[str, str]]


class CommonSettings(Settings):
    """Common settings"""

    PROJECT_ROOT: str
    FILES_PATH: str

    ADMINS: list[int]
    TECH_ADMINS: list[int]
    ADMIN_GROUP_ID: str
    ADMIN_BUGS_GROUP_ID: str

    @computed_field
    def RESOURCES_PATH(self) -> str:  # noqa
        return self.PROJECT_ROOT + "resources/{}"

    @computed_field
    def LOGS_PATH(self) -> str:  # noqa
        return self.PROJECT_ROOT + "logs/"


class DatabaseSettings(Settings):
    """Database settings"""

    SQLALCHEMY_URL: str
    SCHEDULER_URL: str

    TIMEZONE: str

    STORAGE_TABLE_NAME: str

    CUSTOM_BOT_STORAGE_DB_URL: str
    CUSTOM_BOT_STORAGE_TABLE_NAME: str


class MainTelegramBotSettings(Settings):
    """MainTelegramBot settings"""

    TELEGRAM_TOKEN: str
    TEST_PROVIDER_TOKEN: str
    BOT_DEBUG_MODE: bool

    DESTINATION_PHONE_NUMBER: str
    SBP_PAYMENT_URL: str


class CustomTelegramBotSettings(Settings):
    """CustomTelegramBot settings"""

    WEBHOOK_URL: str
    WEBHOOK_HOST: str
    WEBHOOK_PORT: int
    WEBHOOK_LABEL: str

    WEB_APP_URL: str
    WEB_APP_PORT: str

    WEBHOOK_LOCAL_API_URL_HOST: str
    WEBHOOK_LOCAL_API_URL_OUTSIDE: str
    WEBHOOK_LOCAL_API_PORT: int

    WEBHOOK_SERVER_HOST_TO_REDIRECT: str
    WEBHOOK_SERVER_PORT_TO_REDIRECT: int


class LogsSettings(Settings):
    """Logs settings"""

    LOG_TO_GRAFANA: bool
    GRAFANA_URL: str
    FROM: str


class CryptographySettings(Settings):
    """Cryptography settings"""

    TOKEN_SECRET_KEY: str


if __name__ == "__main__":  # You can run this file to ensure in existing of vars
    Settings()
    APISettings()
    CommonSettings()
    DatabaseSettings()
    CryptographySettings()
    MainTelegramBotSettings()
    CustomTelegramBotSettings()
    print(APISettings().model_dump())
