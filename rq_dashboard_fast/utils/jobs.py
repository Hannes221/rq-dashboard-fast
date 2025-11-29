import logging
import warnings
from collections import defaultdict
from datetime import datetime
from typing import Any

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
    scheduled: list[JobData]
    queued: list[JobData]
    started: list[JobData]
    failed: list[JobData]
    deferred: list[JobData]
    finished: list[JobData]


logger = logging.getLogger(__name__)

STATE_FETCHERS_ORDER = (
    ("queued", lambda queue: queue.get_job_ids()),
    ("finished", lambda queue: queue.finished_job_registry.get_job_ids()),
    ("failed", lambda queue: queue.failed_job_registry.get_job_ids()),
    ("started", lambda queue: queue.started_job_registry.get_job_ids()),
    ("deferred", lambda queue: queue.deferred_job_registry.get_job_ids()),
    ("scheduled", lambda queue: queue.scheduled_job_registry.get_job_ids()),
)

STATE_FETCHERS = {name: fetcher for name, fetcher in STATE_FETCHERS_ORDER}


def get_job_registries(
    redis_url: str,
    queue_name: str = "all",
    state: str = "all",
    page: int = 1,
    per_page: int = 10,
) -> list[QueueJobRegistryStats]:
    try:
        redis = Redis.from_url(redis_url)
        scheduler = Scheduler(connection=redis)
        queues = get_queues(redis_url)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        scheduled_jobs_by_origin = _scheduled_jobs_grouped_by_origin(scheduler)
        result: list[QueueJobRegistryStats] = []

        for queue in queues:
            if queue_name != "all" and queue_name != queue.name:
                continue

            job_ids = _job_ids_for_queue(queue, state)
            fetched_jobs = Job.fetch_many(job_ids, connection=redis)[
                start_index:end_index
            ]
            status_lists = {
                "queued": [],
                "started": [],
                "failed": [],
                "deferred": [],
                "finished": [],
            }

            for job in fetched_jobs:
                if job is None:
                    continue
                status = job.get_status()
                target_list = status_lists.get(status)
                if target_list is not None:
                    target_list.append(_job_data_from_job(job))

            result.append(
                QueueJobRegistryStats(
                    queue_name=queue.name,
                    scheduled=scheduled_jobs_by_origin.get(queue.name, []),
                    queued=status_lists["queued"],
                    started=status_lists["started"],
                    failed=status_lists["failed"],
                    deferred=status_lists["deferred"],
                    finished=status_lists["finished"],
                )
            )

        return result
    except Exception as error:
        logger.exception("Error fetching job registries", exc_info=error)
        raise HTTPException(
            status_code=500, detail="Error fetching job registries"
        ) from error


def get_job_registrys(
    redis_url: str,
    queue_name: str = "all",
    state: str = "all",
    page: int = 1,
    per_page: int = 10,
) -> list[QueueJobRegistryStats]:
    warnings.warn(
        "get_job_registrys is deprecated, use get_job_registries instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_job_registries(redis_url, queue_name, state, page, per_page)


def get_jobs(
    redis_url: str, queue_name: str = "all", state: str = "all", page: int = 1
) -> list[QueueJobRegistryStats]:
    try:
        job_stats = get_job_registries(redis_url, queue_name, state, page)
        return job_stats
    except Exception as error:
        logger.exception("Error fetching job data", exc_info=error)
        raise HTTPException(status_code=500, detail="Error fetching job data") from error


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
        logger.exception("Error fetching job", exc_info=error)
        raise HTTPException(status_code=500, detail="Error fetching job") from error


def delete_job_id(redis_url: str, job_id: str):
    try:
        redis = Redis.from_url(redis_url)
        job = Job.fetch(job_id, connection=redis)
        if job:
            job.delete()
    except Exception as error:
        logger.exception("Error deleting specific job", exc_info=error)
        raise HTTPException(
            status_code=500, detail="Error deleting specific job"
        ) from error


def requeue_job_id(redis_url: str, job_id: str):
    try:
        redis = Redis.from_url(redis_url)
        job = Job.fetch(job_id, connection=redis)
        if job:
            job.requeue()
    except Exception as error:
        logger.exception("Error reloading specific job", exc_info=error)
        raise HTTPException(
            status_code=500, detail="Error reloading specific job"
        ) from error


def convert_queue_job_registry_stats_to_json_dict(
    job_data: list[QueueJobRegistryStats],
) -> list[dict[str, Any]]:
    try:
        job_stats_dict = {
            job_stats.queue_name: _serialize_job_stats(job_stats)
            for job_stats in job_data
        }
        return [job_stats_dict]
    except Exception as error:
        logger.exception(
            "Error converting queue job registry stats list to JSON dictionary",
            exc_info=error,
        )
        raise HTTPException(
            status_code=500,
            detail="Error converting queue job registry stats list to JSON dictionary",
        ) from error


def convert_queue_job_registry_dict_to_list(input_data: list[dict]) -> list[dict]:
    try:
        return [
            {
                "id": job["id"],
                "queue_name": queue_name,
                "status": status,
                "job_name": job["name"],
                "created_at": job["created_at"],
            }
            for queue_dict in input_data
            for queue_name, queue_data in queue_dict.items()
            for status, jobs in queue_data.items()
            for job in jobs
        ]
    except Exception as error:
        logger.exception("Error converting job registry stats dict to list", exc_info=error)
        raise HTTPException(
            status_code=500,
            detail="Error converting job registry stats dict to list",
        ) from error


def _job_ids_for_queue(queue, state: str) -> list[str]:
    if state == "all":
        job_ids: list[str] = []
        for name, fetcher in STATE_FETCHERS_ORDER:
            job_ids.extend(fetcher(queue))
        return job_ids

    fetcher = STATE_FETCHERS.get(state)
    return fetcher(queue) if fetcher else []


def _scheduled_jobs_grouped_by_origin(scheduler: Scheduler) -> dict[str, list[JobData]]:
    jobs_by_origin: defaultdict[str, list[JobData]] = defaultdict(list)
    seen_ids: defaultdict[str, set[str]] = defaultdict(set)
    for job in scheduler.get_jobs():
        if job.id in seen_ids[job.origin]:
            continue
        seen_ids[job.origin].add(job.id)
        jobs_by_origin[job.origin].append(_job_data_from_job(job))
    return jobs_by_origin


def _job_data_from_job(job: Job) -> JobData:
    return JobData(
        id=job.id,
        name=job.description,
        created_at=job.created_at,
    )


def _serialize_job_stats(job_stats: QueueJobRegistryStats) -> dict[str, list[dict[str, Any]]]:
    def job_data_to_dict(job_data: JobData) -> dict[str, Any]:
        return {
            "id": job_data.id,
            "name": job_data.name,
            "created_at": job_data.created_at.isoformat(),
        }

    return {
        "scheduled": [job_data_to_dict(job) for job in job_stats.scheduled],
        "queued": [job_data_to_dict(job) for job in job_stats.queued],
        "started": [job_data_to_dict(job) for job in job_stats.started],
        "failed": [job_data_to_dict(job) for job in job_stats.failed],
        "deferred": [job_data_to_dict(job) for job in job_stats.deferred],
        "finished": [job_data_to_dict(job) for job in job_stats.finished],
    }
