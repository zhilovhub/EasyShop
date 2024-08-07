from database.models.models import Database
from database.models.partnership_model import PartnershipSchemaWithoutId, CriteriaSchemaWithoutId

from common_utils.config import database_settings
from common_utils.singleton import singleton
from common_utils.scheduler.scheduler import Scheduler

from logs.config import logger, extra_params


@singleton
class Partnership:
    """Модуль системы партнерства"""

    def __init__(self, database: Database, custom_scheduler: Scheduler) -> None:
        self.user_db = database.get_user_dao()
        self.partnership_db = database.get_partnership_dao()

        self.scheduler = custom_scheduler

    async def start_partnership(self, partnership_id: int):
        await self.partnership_db.get_partnership_by_id(partnership_id)

    async def create_partnership(self, bot_id: int, post_message_id: int, price: int,
                                 criteria: CriteriaSchemaWithoutId) -> int:
        logger.info(f"bot_id={bot_id} : creating new criteria for partnership",
                    exc_info=extra_params(bot_id=bot_id, post_message_id=post_message_id))
        criteria_id = await self.partnership_db.add_partnership_criteria(criteria)

        new_partnership = PartnershipSchemaWithoutId(bot_id=bot_id,
                                                     post_message_id=post_message_id,
                                                     price=price,
                                                     criteria_id=criteria_id)
        logger.info(f"bot_id={bot_id} : creating new partnership",
                    exc_info=extra_params(bot_id=bot_id, post_message_id=post_message_id))
        partnership_id = await self.partnership_db.add_partnership(new_partnership)

        return partnership_id


if __name__ == '__main__':
    from database.models.models import Database

    scheduler = Scheduler(database_settings.SCHEDULER_URL, 'postgres', database_settings.TIMEZONE)
