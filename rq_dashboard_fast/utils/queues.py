import logging

from fastapi import HTTPException
from pydantic import BaseModel
from redis import Redis
from rq import Queue

import pandas


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
        logger.exception("Error reading Queues for redis connection: ", error)
        raise HTTPException(
            status_code=500,
            detail=str("Error reading Queues for redis connection: ", error),
        )


def get_job_registry_amount(redis_url: str) -> list[QueueRegistryStats]:
    try:
        queues = get_queues(redis_url)
        result = []
        for queue in queues:
            finished_jobs = len(queue.finished_job_registry.get_job_ids())
            started_jobs = len(queue.started_job_registry.get_job_ids())
            failed_jobs = len(queue.failed_job_registry.get_job_ids())
            deferred_jobs = len(queue.deferred_job_registry.get_job_ids())
            queued_jobs = len(queue.get_job_ids())

            result.append(
                QueueRegistryStats(
                    queue_name=queue.name,
                    queued=queued_jobs,
                    started=started_jobs,
                    failed=failed_jobs,
                    deferred=deferred_jobs,
                    finished=finished_jobs,
                )
            )
        return result
    except Exception as error:
        logger.exception("Error reading registrys for queue: ", error)
        raise HTTPException(
            status_code=500, detail=str("Error reading registrys for queue: ", error)
        )


def delete_jobs_for_queue(queue_name, redis_url) -> list[str]:
    try:
        redis = Redis.from_url(redis_url)

        queue = Queue(queue_name, connection=redis)

        result = queue.empty()

        return result
    except Exception as error:
        logger.exception("Error deleting jobs in queue: ", error)
        raise HTTPException(
            status_code=500, detail=str("Error deleting jobs in queue: ", error)
        )
def convert_queue_data_to_json_dict(queue_data: list[QueueRegistryStats]) -> list[dict]:
    try:
        queue_stats_dict = {}
        for queue_stats in queue_data:
            stats_dict = {
                'queued': queue_stats.queued,
                'started': queue_stats.started,
                'failed': queue_stats.failed,
                'deferred': queue_stats.deferred,
                'finished': queue_stats.finished
            }
            queue_stats_dict[queue_stats.queue_name] = stats_dict

        queue_stats_list = [queue_stats_dict]
        return queue_stats_list
    except Exception as error:
        logger.exception("Error converting queue items list to JSON dictionary: ", error)
        raise Exception(f"Error converting queue items list to JSON dictionary: {str(error)}")
def convert_queues_dict_to_dataframe(input_data: list[dict]) -> pandas.DataFrame:
    queue_details = []
    try:
        for queue_dict in input_data:
            for queue_name, queue_data in queue_dict.items():
                for status, count in queue_data.items():
                            queue_info = {
                                "queue_name": queue_name,
                                "status": status,
                                "count": count
                            }
                            queue_details.append(queue_info)
        df = pandas.DataFrame(queue_details)
        return df
    except Exception as error:
            logger.exception("Error converting queues dict to DataFrame: ", error)
            raise Exception(f"Error converting queues dict to DataFrame: {str(error)}")