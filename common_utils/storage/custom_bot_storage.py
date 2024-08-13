from common_utils.config import database_settings
from common_utils.storage.storage import AlchemyStorageAsync

custom_bot_storage = AlchemyStorageAsync(
    db_url=database_settings.CUSTOM_BOT_STORAGE_DB_URL, table_name=database_settings.CUSTOM_BOT_STORAGE_TABLE_NAME
)
