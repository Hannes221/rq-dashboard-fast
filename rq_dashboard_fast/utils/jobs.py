import logging
from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from redis import Redis
from rq.job import Job
from rq_scheduler import Scheduler

from .queues import get_queues

router = APIRouter()


class JobData(BaseModel):
    id: str
    name: str
    created_at: datetime


class JobDataDetailed(BaseModel):
    id: str
    name: str
    created_at: datetime
    enqueued_at: datetime | None
    ended_at: datetime | None
    result: Any
    exc_info: str | None
    meta: dict


class QueueJobRegistryStats(BaseModel):
    queue_name: str
    scheduled: List[JobData]
    queued: List[JobData]
    started: List[JobData]
    failed: List[JobData]
    deferred: List[JobData]
    finished: List[JobData]


logger = logging.getLogger(__name__)


def get_job_registrys(
    redis_url: str,
    queue_name: str = "all",
    state: str = "all",
    page: int = 1,
    per_page: int = 10,
) -> List[QueueJobRegistryStats]:
    try:
        redis = Redis.from_url(redis_url)
        scheduler = Scheduler(connection=redis, queue_name=queue_name)

        queues = get_queues(redis_url)
        result = []

        start_index = (page - 1) * per_page
        end_index = start_index + per_page

        scheduled_jobs = []

        for queue in queues:
            if queue_name == "all" or queue_name == queue.name:
                jobs = []

                if state == "all":
                    jobs.extend(queue.get_job_ids())
                    jobs.extend(queue.finished_job_registry.get_job_ids())
                    jobs.extend(queue.failed_job_registry.get_job_ids())
                    jobs.extend(queue.started_job_registry.get_job_ids())
                    jobs.extend(queue.deferred_job_registry.get_job_ids())
                elif state == "scheduled":
                    jobs.extend(queue.scheduled_job_registry.get_job_ids())
                elif state == "queued":
                    jobs.extend(queue.get_job_ids())
                elif state == "finished":
                    jobs.extend(queue.finished_job_registry.get_job_ids())
                elif state == "failed":
                    jobs.extend(queue.failed_job_registry.get_job_ids())
                elif state == "started":
                    jobs.extend(queue.started_job_registry.get_job_ids())
                elif state == "deferred":
                    jobs.extend(queue.deferred_job_registry.get_job_ids())

                if state == "all" or state == "scheduled":
                    scheduled = scheduler.get_jobs()

                    for job in scheduled:
                        scheduled_jobs.append(
                            JobData(
                                id=job.id,
                                name=job.description,
                                created_at=job.created_at,
                            )
                        )

                jobs_fetched = Job.fetch_many(jobs, connection=redis)

                started_jobs = []
                failed_jobs = []
                deferred_jobs = []
                finished_jobs = []
                queued_jobs = []
                scheduled_jobs = []

                for job in jobs_fetched[start_index:end_index]:
                    status = job.get_status()
                    if status == "started":
                        started_jobs.append(
                            JobData(
                                id=job.id,
                                name=job.description,
                                created_at=job.created_at,
                            )
                        )
                    elif status == "failed":
                        failed_jobs.append(
                            JobData(
                                id=job.id,
                                name=job.description,
                                created_at=job.created_at,
                            )
                        )
                    elif status == "deferred":
                        deferred_jobs.append(
                            JobData(
                                id=job.id,
                                name=job.description,
                                created_at=job.created_at,
                            )
                        )
                    elif status == "finished":
                        finished_jobs.append(
                            JobData(
                                id=job.id,
                                name=job.description,
                                created_at=job.created_at,
                            )
                        )
                    elif status == "queued":
                        queued_jobs.append(
                            JobData(
                                id=job.id,
                                name=job.description,
                                created_at=job.created_at,
                            )
                        )

                result.append(
                    QueueJobRegistryStats(
                        queue_name=queue.name,
                        scheduled=scheduled_jobs,
                        queued=queued_jobs,
                        started=started_jobs,
                        failed=failed_jobs,
                        deferred=deferred_jobs,
                        finished=finished_jobs,
                    )
                )

        return result
    except Exception as error:
        logger.exception("Error fetching job registries: ", error)
        raise HTTPException(
            status_code=500, detail=str("Error fetching job registries: ", error)
        )


def get_jobs(
    redis_url: str, queue_name: str = "all", state: str = "all", page: int = 1
) -> list[QueueJobRegistryStats]:
    try:
        job_stats = get_job_registrys(redis_url, queue_name, state, page)
        return job_stats
    except Exception as error:
        logger.exception("Error fetching job data: ", error)
        raise HTTPException(
            status_code=500, detail=str("Error fetching job data: ", error)
        )


def get_job(redis_url: str, job_id: str) -> JobDataDetailed:
    try:
        redis = Redis.from_url(redis_url)
        job = Job.fetch(job_id, connection=redis)

        return JobDataDetailed(
            id=job.id,
            name=job.description,
            created_at=job.created_at,
            enqueued_at=job.enqueued_at,
            ended_at=job.ended_at,
            result=job.result,
            exc_info=job.exc_info,
            meta=job.meta,
        )
    except Exception as error:
        logger.exception("Error fetching job: ", error)
        raise HTTPException(status_code=500, detail=str("Error fetching job: ", error))


def delete_job_id(redis_url: str, job_id: str):
    try:
        redis = Redis.from_url(redis_url)
        job = Job.fetch(job_id, connection=redis)
        if job:
            job.delete()
    except Exception as error:
        logger.exception("Error deleting specific job: ", error)
        raise HTTPException(
            status_code=500, detail=str("Error deleting specific job: ", error)
        )
