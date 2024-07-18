try:
    from database.models.models import Database
    from database.models.user_model import UserStatusValues

    from common_utils.env_config import TIMEZONE, SQLALCHEMY_URL, SCHEDULER_URL
    from common_utils.scheduler.scheduler import Scheduler
    from common_utils.subscription.subscription import Subscription

    from logs.config import logger, extra_params


    from bot.handlers.subscription_handlers import send_subscription_expire_notify, send_subscription_end_notify
except ImportError as ex:
    print(f"IMPORT ERROR: if running module from terminal please set PYTHONPATH env variable to project root")
    exit(1)

import asyncio
from datetime import datetime


class UserIsNotSubscribed(Exception):
    pass


class NewDateMustBeInFuture(Exception):
    pass


class IncorrectParamType(Exception):
    pass


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


@singleton
class Administration:
    """Модуль системы администрации"""

    def __init__(self, database: Database, custom_scheduler: Scheduler, subscription: Subscription) -> None:
        self.user_db = database.get_user_dao()
        self.scheduler = custom_scheduler
        self.subscription = subscription

    async def _delete_jobs(self, job_ids: list[str], user_id: int):
        logger.info(f"deleting old jobs for user ({user_id})")
        for job_id in job_ids:
            await self.scheduler.del_job_by_id(job_id)

    async def change_sub_until_date(self, user_id: int, new_date: datetime) -> list[str]:
        user = await self.user_db.get_user(user_id)

        if not (user.status in (UserStatusValues.TRIAL, UserStatusValues.SUBSCRIBED)):
            raise UserIsNotSubscribed
        if new_date < datetime.now():
            raise NewDateMustBeInFuture

        user.subscribed_until = new_date
        await self._delete_jobs(user.subscription_job_ids, user_id)

        logger.info(f"creating new jobs with new date ({new_date}) for user ({user_id})")
        new_jobs = await self.subscription.add_notifications(
            user_id,
            on_expiring_notification=send_subscription_expire_notify,
            on_end_notification=send_subscription_end_notify,
            subscribed_until=new_date
        )
        user.subscription_job_ids = new_jobs

        await self.user_db.update_user(user)

        return new_jobs

    async def change_sub_status(self, user_id: int, is_subscribed: bool):
        user = await self.user_db.get_user(user_id)
        if is_subscribed:
            user.status = UserStatusValues.SUBSCRIBED
        else:
            user.status = UserStatusValues.SUBSCRIPTION_ENDED
            await self._delete_jobs(user.subscription_job_ids, user_id)
        await self.user_db.update_user(user)


if __name__ == "__main__":
    import sys

    logger.info(f"Administration module started from terminal with params {sys.argv}.")

    scheduler = Scheduler(scheduler_url=SCHEDULER_URL, jobstore_alias='postgres', timezone=TIMEZONE)
    database = Database(sqlalchemy_url=SQLALCHEMY_URL, logger=logger)
    administration = Administration(
        database=database,
        custom_scheduler=scheduler,
        subscription=Subscription(database, scheduler)
    )

    available_commands = ("\n\nset_sub_until [user_id] [timestamp int] - меняет дату окончания подписки юзера"
                          "\n\nset_sub [user_id] [True/False] - устанавливает подписку юзера"
                          "\n")

    if len(sys.argv) == 1:
        print(f"\nARGUMENT NOT PROVIDED ERROR:\n"
              f"FORMAT: python3 administration.py [command] [options...]{available_commands}")
        exit(2)

    def _check_params(params: list[str], params_types: list) -> list:
        return_params = []
        for ind, param in enumerate(params):
            if params_types[ind] == bool:
                if param.lower() == "true":
                    return_params.append(True)
                elif param.lower() == "false":
                    return_params.append(False)
                else:
                    raise IncorrectParamType(f"{param} must be {params_types[ind]}")
            elif params_types[ind] == int:
                try:
                    return_params.append(int(param))
                except Exception:
                    raise IncorrectParamType(f"{param} must be {params_types[ind]}")
        return return_params

    match sys.argv[1]:
        case "set_sub_until":
            if len(sys.argv) != 4:
                print("NOT ENOUGH PARAMS:\nFORMAT: \npython3 administration.pyset_sub_until [user_id] [timestamp int]")
                exit(4)
            formatted_params = _check_params(sys.argv[2:4], [int, int])
            formatted_params[-1] = datetime.fromtimestamp(formatted_params[-1])
            asyncio.run(administration.change_sub_until_date(*formatted_params))
        case "set_sub":
            if len(sys.argv) != 4:
                print("NOT ENOUGH PARAMS:\nFORMAT: \npython3 administration.pyset_sub_until [user_id] [timestamp int]")
                exit(4)
            formatted_params = _check_params(sys.argv[2:4], [int, bool])
            asyncio.run(administration.change_sub_status(*formatted_params))
        case _:
            print(f"UNKNOWN COMMAND ERROR:{available_commands}")
            exit(3)
