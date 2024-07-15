from common_utils.env_config import SQLALCHEMY_URL

from database.models.models import Database


if __name__ == '__main__':
    db = Database(sqlalchemy_url=SQLALCHEMY_URL)
