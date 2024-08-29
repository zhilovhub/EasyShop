import string
import random
from typing import Callable
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from common_utils.config import database_settings
from common_utils.singleton import singleton

from logs.config import logger, extra_params


@singleton
class Scheduler:
    def __init__(self, scheduler_url: str, jobstore_alias: str, timezone: str, tablename: str = "apscheduler_jobs"):
        self.scheduler = AsyncIOScheduler(
            {"apscheduler.timezone": database_settings.TIMEZONE},
            jobstores={jobstore_alias: SQLAlchemyJobStore(url=scheduler_url, tablename=tablename)},
        )
        self.jobstore_alias = jobstore_alias
        self.timezone = timezone
        self.table_name = tablename
        # self.scheduler.add_job(func=print, trigger='interval', args=['Test'], seconds=5, jobstore=self.jobstore_alias)

    async def start(self):
        self.scheduler.start()
        logger.info(f"Scheduler started with previous jobs: {await self.get_jobs()}")

    async def change_job(self, job, changes):
        logger.debug(f"job_id={job.id}: job changed by {changes}", extra=extra_params(job_id=job.id))
        return await self.scheduler.modify_job(job_id=job.id, jobstore=self.jobstore_alias, **changes)

    async def get_jobs(self):
        jobs = self.scheduler.get_jobs(jobstore=self.jobstore_alias)
        logger.debug(f"Scheduler returned {len(jobs)} jobs: {jobs}")
        return jobs

    async def get_job(self, job_id: str):
        job = self.scheduler.get_job(job_id=job_id, jobstore=self.jobstore_alias)

        if job:
            logger.debug(f"job_id={job_id}: found {job}", extra=extra_params(job_id=job_id))
        else:
            logger.warning(f"job_id={job_id}: this job is not found", extra=extra_params(job_id=job_id))

        return job

    async def del_job(self, job):
        logger.debug(f"job_id={job.id}: the job has been deleted", extra=extra_params(job_id=job.id))
        return self.scheduler.remove_job(job_id=job.id, jobstore=self.jobstore_alias)

    async def del_job_by_id(self, job_id: str):
        logger.debug(f"job_id={job_id}: the job has been deleted", extra=extra_params(job_id=job_id))
        return self.scheduler.remove_job(job_id=job_id, jobstore=self.jobstore_alias)

    async def generate_job_id(self, length: int = 10) -> str:
        letters = string.ascii_letters
        new_id = "".join(random.choice(letters) for _ in range(length))
        if not await self.get_job(new_id):
            logger.debug(f"job_id={new_id}: the job_id={new_id} has been generated", extra=extra_params(job_id=new_id))
            return new_id
        return await self.generate_job_id(length)

    async def add_scheduled_job(
        self, func: Callable, run_date: datetime, args: list | tuple, job_id: str | None = None
    ) -> str:
        if not job_id:
            job_id = await self.generate_job_id()

        try:
            self.scheduler.add_job(
                func=func,
                trigger="date",
                run_date=run_date,
                args=args,
                id=job_id,
                jobstore=self.jobstore_alias,
                timezone=self.timezone,
            )
            logger.debug(
                f"job_id={job_id}: new job with func={func}, run_date={run_date}, args={args} has been scheduled",
                extra=extra_params(job_id=job_id),
            )
            return job_id
        except Exception as e:
            logger.error(
                f"job_id={job_id}: new job with func={func}, run_date={run_date}, args={args} has not been scheduled",
                extra=extra_params(job_id=job_id),
                exc_info=e,
            )
            raise e

    async def stop_scheduler(self):
        self.scheduler.shutdown()
        logger.debug(
            "Scheduler has been stopped",
        )

    def clear_table(self) -> None:
        """
        Often used in tests
        """
        self.scheduler.remove_all_jobs(jobstore=self.jobstore_alias)

        logger.debug(f"Table {self.table_name} has been cleared")
