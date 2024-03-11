import logging
from apscheduler.jobstores.base import ConflictingIdError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from bot import config
import logging
import logging.config
from typing import Callable
from datetime import datetime, timedelta
import string
import random


logging.config.dictConfig(config.LOGGING_SETUP)
logger = logging.getLogger('logger')


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


@singleton
class Scheduler:

    def __init__(self, scheduler: AsyncIOScheduler, jobstore_alias: str, timezone: str):
        self.scheduler = scheduler
        self.jobstore_alias = jobstore_alias
        self.timezone = timezone
        # self.scheduler.add_job(func=print, trigger='interval', args=['Test'], seconds=5, jobstore=self.jobstore_alias)

    async def start(self):
        self.scheduler.start()
        logger.info(f"Scheduler started with previous jobs: {await self.get_jobs()}")

    async def change_job(self, job, changes):
        return await self.scheduler.modify_job(job_id=job.id, jobstore=self.jobstore_alias, **changes)

    async def get_jobs(self):
        return self.scheduler.get_jobs(jobstore=self.jobstore_alias)

    async def get_job(self, job_id: str):
        return self.scheduler.get_job(job_id=job_id, jobstore=self.jobstore_alias)

    async def del_job(self, job):
        return self.scheduler.remove_job(job_id=job.id, jobstore=self.jobstore_alias)

    async def del_job_by_id(self, job_id: str):
        return self.scheduler.remove_job(job_id=job_id, jobstore=self.jobstore_alias)

    async def generate_job_id(self, length: int = 10) -> str:
        letters = string.ascii_letters
        new_id = ''.join(random.choice(letters) for _ in range(length))
        if not await self.get_job(new_id):
            return new_id
        return await self.generate_job_id(length)

    async def add_scheduled_job(self, func: Callable, run_date: datetime, args: list | tuple, job_id: str | None = None) -> str:
        if not job_id:
            job_id = await self.generate_job_id()
        logger.info(f"New scheduled task on date ({run_date}) with id ({job_id})")
        try:
            self.scheduler.add_job(func=func, trigger='date', run_date=run_date, args=args, id=job_id,
                                   jobstore=self.jobstore_alias,
                                   timezone=self.timezone)
            return job_id
        except Exception:
            logger.error("error while adding scheduled job", exc_info=True)
            raise

    async def stop_scheduler(self):
        self.scheduler.shutdown()
