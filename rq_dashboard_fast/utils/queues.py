import logging

from fastapi import HTTPException
from pydantic import BaseModel
from redis import Redis
from rq import Queue


class QueueRegistryStats(BaseModel):
    queue_name: str
    queued: int
    started: int
    failed: int
    deferred: int
    finished: int


logger = logging.getLogger(__name__)


def get_queues(redis_url: str) -> list[Queue]:
    try:
        redis = Redis.from_url(redis_url)

        queues = Queue.all(connection=redis)

        return queues
    except Exception as error:
        logger.exception("Error reading Queues for redis connection", exc_info=error)
        raise HTTPException(
            status_code=500, detail="Error reading Queues for redis connection"
        ) from error


def get_job_registry_amount(redis_url: str) -> list[QueueRegistryStats]:
    try:
        queues = get_queues(redis_url)
        return [
            QueueRegistryStats(
                queue_name=queue.name,
                queued=len(queue.get_job_ids()),
                started=len(queue.started_job_registry.get_job_ids()),
                failed=len(queue.failed_job_registry.get_job_ids()),
                deferred=len(queue.deferred_job_registry.get_job_ids()),
                finished=len(queue.finished_job_registry.get_job_ids()),
            )
            for queue in queues
        ]
    except Exception as error:
        logger.exception("Error reading registrys for queue", exc_info=error)
        raise HTTPException(
            status_code=500, detail="Error reading registrys for queue"
        ) from error


def delete_jobs_for_queue(queue_name, redis_url) -> list[str]:
    try:
        redis = Redis.from_url(redis_url)

        queue = Queue(queue_name, connection=redis)

        result = queue.empty()

        return result
    except Exception as error:
        logger.exception("Error deleting jobs in queue", exc_info=error)
        raise HTTPException(
            status_code=500, detail="Error deleting jobs in queue"
        ) from error


def convert_queue_data_to_json_dict(queue_data: list[QueueRegistryStats]) -> list[dict]:
    try:
        queue_stats_dict = {
            queue_stats.queue_name: {
                "queued": queue_stats.queued,
                "started": queue_stats.started,
                "failed": queue_stats.failed,
                "deferred": queue_stats.deferred,
                "finished": queue_stats.finished,
            }
            for queue_stats in queue_data
        }
        return [queue_stats_dict]
    except Exception as error:
        logger.exception(
            "Error converting queue items list to JSON dictionary",
            exc_info=error,
        )
        raise HTTPException(
            status_code=500,
            detail="Error converting queue items list to JSON dictionary",
        ) from error


def convert_queues_dict_to_list(input_data: list[dict]) -> list[dict]:
    try:
        return [
            {
                "queue_name": queue_name,
                "status": status,
                "count": count,
            }
            for queue_dict in input_data
            for queue_name, queue_data in queue_dict.items()
            for status, count in queue_data.items()
        ]
    except Exception as error:
        logger.exception("Error converting queues dict to list", exc_info=error)
        raise HTTPException(
            status_code=500, detail="Error converting queues dict to list"
        ) from error
