import pytest
from rq import Queue
from redis import Redis
from rq_scheduler import Scheduler
from datetime import datetime
from ..utils.jobs import (
    get_job_registrys,
    get_jobs,
    get_job,
    delete_job_id,
    convert_queue_job_registry_stats_to_json,
    JobData,
    QueueJobRegistryStats
)
import json

@pytest.fixture
def setup_redis():
    redis = Redis(port=6379, host="redis")
    yield redis


@pytest.fixture
def setup_scheduler(setup_redis):
    scheduler = Scheduler(connection=setup_redis)
    yield scheduler


@pytest.fixture
def setup_queue(setup_redis):
    queue = Queue(connection=setup_redis)
    yield queue


def example_task():
    return "Hello World"


def test_get_job_registrys(setup_redis, setup_scheduler, setup_queue):
    redis_url = "redis://redis:6379"
    job_name = "test_job"
    job = setup_queue.enqueue(example_task, description=job_name)

    job_registrys = get_job_registrys(redis_url)

    assert any(
        queue_job.queue_name == setup_queue.name
        and any(job_data.name == job_name for job_data in queue_job.queued)
        for queue_job in job_registrys
    )


def test_get_jobs(setup_redis, setup_scheduler, setup_queue):
    redis_url = "redis://redis:6379"
    job_name = "test_job1"
    job = setup_queue.enqueue(example_task, description=job_name)

    jobs = get_jobs(redis_url)

    assert any(
        job_data.name == job_name for queue_job in jobs for job_data in queue_job.queued
    )


def test_get_job(setup_redis, setup_queue):
    redis_url = "redis://redis:6379"
    job_name = "test_job2"
    job = setup_queue.enqueue(example_task, description=job_name)

    job_data = get_job(redis_url, job.id)

    assert job_data.name == job_name


def test_delete_job_id(setup_redis, setup_queue):
    redis_url = "redis://redis:6379"
    job_name = "test_job3"
    job = setup_queue.enqueue(example_task, description=job_name)

    delete_job_id(redis_url, job.id)

    assert not setup_queue.fetch_job(job.id)

def test_convert_queue_job_registry_stats_to_json():
        job_data_1 = JobData(id='1', name='Job 1', created_at='2020-01-01')
        job_data_2 = JobData(id='2', name='Job 2', created_at='2020-01-01')
        
        queue_stats_1 = QueueJobRegistryStats(queue_name='Queue 1', 
                                             scheduled=[job_data_1], 
                                             queued=[job_data_2], 
                                             started=[], 
                                             failed=[], 
                                             deferred=[], 
                                             finished=[])
        
        queue_stats_2 = QueueJobRegistryStats(queue_name='Queue 2', 
                                             scheduled=[], 
                                             queued=[], 
                                             started=[job_data_1, job_data_2], 
                                             failed=[], 
                                             deferred=[], 
                                             finished=[])
        queue_data = [queue_stats_1, queue_stats_2]
        result_json = convert_queue_job_registry_stats_to_json(queue_data)
        expected_json_string = """
        [
            {
                "Queue 1": {
                    "scheduled": [
                        {
                            "id": "1",
                            "name": "Job 1",
                            "created_at": "2020-01-01T00:00:00"
                        }
                    ],
                    "queued": [
                        {
                            "id": "2",
                            "name": "Job 2",
                            "created_at": "2020-01-01T00:00:00"
                        }
                    ],
                    "started": [],
                    "failed": [],
                    "deferred": [],
                    "finished": []
                },
                "Queue 2": {
                    "scheduled": [],
                    "queued": [],
                    "started": [
                        {
                            "id": "1",
                            "name": "Job 1",
                            "created_at": "2020-01-01T00:00:00"
                        },
                        {
                            "id": "2",
                            "name": "Job 2",
                            "created_at": "2020-01-01T00:00:00"
                        }
                    ],
                    "failed": [],
                    "deferred": [],
                    "finished": []
                }
            }
        ]
        """
        expected_result = json.loads(expected_json_string)
        actual_result = json.loads(result_json)

        assert actual_result == expected_result
