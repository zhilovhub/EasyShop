from database.models.models import Database

from config import SQLALCHEMY_URL


if __name__ == '__main__':
    db = Database(sqlalchemy_url=SQLALCHEMY_URL)
    # asyncio.run(db.get_product_db().method())
