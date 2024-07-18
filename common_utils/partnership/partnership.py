from datetime import datetime, timedelta

from database.models.models import Database

from common_utils.partnership import config
from common_utils.singleton import singleton
from common_utils.scheduler.scheduler import Scheduler
from common_utils.env_config import TIMEZONE, DB_FOR_TESTS, SCHEDULER_URL

from logs.config import logger, extra_params


@singleton
class Partnership:
    """Модуль системы партнерства"""

    def __init__(self, database: Database, custom_scheduler: Scheduler) -> None:
        self.user_db = database.get_user_dao()
        self.partnership_db = database.get_partnership_dao()

        self.scheduler = custom_scheduler


if __name__ == '__main__':
    from database.models.models import Database

    scheduler = Scheduler(SCHEDULER_URL, 'postgres', TIMEZONE)

    subscription = Partnership(
        database=Database(sqlalchemy_url=DB_FOR_TESTS, logger=logger),
        custom_scheduler=scheduler,
    )
