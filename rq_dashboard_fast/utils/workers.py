import logging

from fastapi import HTTPException
from pydantic import BaseModel
from redis import Redis
from rq import Worker
import json

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
        result = []

        for worker in workers:
            current_job = worker.get_current_job()
            if current_job is not None:
                result.append(
                    WorkerData(
                        name=worker.name,
                        current_job=current_job.description,
                        current_job_id=current_job.id,
                        successful_job_count=worker.successful_job_count,
                        failed_job_count=worker.failed_job_count,
                        queues=worker.queue_names(),
                    )
                )
            else:
                result.append(
                    WorkerData(
                        name=worker.name,
                        current_job="Idle",
                        current_job_id=None,
                        successful_job_count=worker.successful_job_count,
                        failed_job_count=worker.failed_job_count,
                        queues=worker.queue_names(),
                    )
                )

        return result
    except Exception as error:
        logger.exception("Error reading workers for redis connection: ", error)
        raise HTTPException(
            status_code=500,
            detail=str("Error reading workers for redis connection: ", error),
        )
def convert_worker_data_to_json(worker_data: list[WorkerData]) -> str:
    try:
        workers_dict = {}
        for worker in worker_data:
            worker_dict = {
                'name': worker.name,
                'current_job': worker.current_job,
                'current_job_id': worker.current_job_id,
                'successful_job_count': worker.successful_job_count,
                'failed_job_count': worker.failed_job_count,
                'queues': worker.queues
            }
            workers_dict[worker.name] = worker_dict

        workers_list = [workers_dict]
        json_str = json.dumps(workers_list, indent=4)
        return json_str
    except Exception as error:
        logger.exception("Error converting worker data list to JSON: ", error)
        raise HTTPException(
            status_code=500, detail=str("Error converting worker data list to JSON: ", error)
        )