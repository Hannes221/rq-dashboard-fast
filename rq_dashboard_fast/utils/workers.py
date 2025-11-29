import logging

from fastapi import HTTPException
from pydantic import BaseModel
from redis import Redis
from rq import Worker

logger = logging.getLogger(__name__)


class WorkerData(BaseModel):
    name: str
    current_job: str | None
    current_job_id: str | None
    successful_job_count: int
    failed_job_count: int
    queues: list[str]


def get_workers(redis_url: str) -> list[WorkerData]:
    try:
        redis = Redis.from_url(redis_url)
        workers = Worker.all(connection=redis)
        return [_format_worker(worker) for worker in workers]
    except Exception as error:
        logger.exception("Error reading workers for redis connection", exc_info=error)
        raise HTTPException(
            status_code=500, detail="Error reading workers for redis connection"
        ) from error


def convert_worker_data_to_json_dict(worker_data: list[WorkerData]) -> list[dict]:
    try:
        workers_dict = {
            worker.name: {
                "name": worker.name,
                "current_job": worker.current_job,
                "current_job_id": worker.current_job_id,
                "successful_job_count": worker.successful_job_count,
                "failed_job_count": worker.failed_job_count,
                "queues": worker.queues,
            }
            for worker in worker_data
        }
        return [workers_dict]
    except Exception as error:
        logger.exception(
            "Error converting worker data list to JSON dictionary", exc_info=error
        )
        raise HTTPException(
            status_code=500,
            detail="Error converting worker data list to JSON dictionary",
        ) from error


def convert_workers_dict_to_list(input_data: list[dict]) -> list[dict]:
    try:
        return [
            {
                "worker_name": worker_name,
                "current_job": worker_data["current_job"],
                "current_job_id": worker_data["current_job_id"],
                "successful_job_count": worker_data["successful_job_count"],
                "failed_job_count": worker_data["failed_job_count"],
                "queue_name": worker_data["queues"],
            }
            for workers_dict in input_data
            for worker_name, worker_data in workers_dict.items()
        ]
    except Exception as error:
        logger.exception("Error converting workers dict to list", exc_info=error)
        raise HTTPException(
            status_code=500, detail="Error converting workers dict to list"
        ) from error


def _format_worker(worker: Worker) -> WorkerData:
    current_job = worker.get_current_job()
    if current_job is None:
        return WorkerData(
            name=worker.name,
            current_job="Idle",
            current_job_id=None,
            successful_job_count=worker.successful_job_count,
            failed_job_count=worker.failed_job_count,
            queues=worker.queue_names(),
        )

    return WorkerData(
        name=worker.name,
        current_job=current_job.description,
        current_job_id=current_job.id,
        successful_job_count=worker.successful_job_count,
        failed_job_count=worker.failed_job_count,
        queues=worker.queue_names(),
    )
