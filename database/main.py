from common_utils.config import database_settings

from database.models.models import Database


if __name__ == '__main__':
    db = Database(sqlalchemy_url=database_settings.SQLALCHEMY_URL)
