import logging
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from redis import Redis
from rq.job import Job
from rq_scheduler import Scheduler
import pandas

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
                    jobs.extend(queue.scheduled_job_registry.get_job_ids())
                else:
                    if state == "scheduled":
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

                started_jobs = []
                failed_jobs = []
                deferred_jobs = []
                finished_jobs = []
                queued_jobs = []
                scheduled_jobs = []

                scheduled = scheduler.get_jobs()

                for job in scheduled:
                    if job.id not in scheduled_jobs:
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

                jobs = jobs_fetched[start_index:end_index]
                for job in jobs:
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
                    elif status == "scheduled":
                        scheduled_jobs.append(
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

def convert_queue_job_registry_stats_to_json_dict(job_data: List[QueueJobRegistryStats]) -> list[dict]:
    try:
        job_stats_dict = {}
        
        for job_stats in job_data:
            def job_data_to_dict(job_data: JobData):
                return {
                    'id': job_data.id,
                    'name': job_data.name,
                    'created_at': job_data.created_at.isoformat()
                }

            stats_dict = {
                'scheduled': [job_data_to_dict(job) for job in job_stats.scheduled],
                'queued': [job_data_to_dict(job) for job in job_stats.queued],
                'started': [job_data_to_dict(job) for job in job_stats.started],
                'failed': [job_data_to_dict(job) for job in job_stats.failed],
                'deferred': [job_data_to_dict(job) for job in job_stats.deferred],
                'finished': [job_data_to_dict(job) for job in job_stats.finished]
            }
            job_stats_dict[job_stats.queue_name] = stats_dict
            queue_stats_list = [job_stats_dict]

        return queue_stats_list
    except Exception as error:
        logger.exception("Error converting queue job registry stats list to JSON dictionary: ", error)
        raise Exception(f"Error converting queue job registry stats list to JSON dictionary: {str(error)}")
def convert_queue_job_registry_dict_to_dataframe(input_data: list[dict]) -> pandas.DataFrame:
    job_details = []
    try:
        for queue_dict in input_data:
            for queue_name, queue_data in queue_dict.items():
                for status, jobs in queue_data.items():
                        for job in jobs:
                            job_info = {
                                "id": job['id'],
                                "queue_name": queue_name,
                                "status": status,
                                "job_name": job['name'],
                                "created_at": job['created_at']
                            }
                            job_details.append(job_info)

        df = pandas.DataFrame(job_details)
        return df
    except Exception as error:
        logger.exception("Error converting job registry stats dict to DataFrame: ", error)
        raise Exception(f"Error converting job registry stats dict to DataFrame: {str(error)}")