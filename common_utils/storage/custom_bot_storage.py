from common_utils.env_config import CUSTOM_BOT_STORAGE_DB_URL, CUSTOM_BOT_STORAGE_TABLE_NAME
from common_utils.storage.storage import AlchemyStorageAsync

custom_bot_storage = AlchemyStorageAsync(
    db_url=CUSTOM_BOT_STORAGE_DB_URL,
    table_name=CUSTOM_BOT_STORAGE_TABLE_NAME
)
