import threading

import pytest
from redis import Redis
from rq import Worker

from ..utils.workers import (
    WorkerData,
    convert_worker_data_to_json_dict,
    convert_workers_dict_to_list,
)

worker_name = "test"


@pytest.fixture
def setup_redis():
    redis = Redis(port=6379, host="redis")
    yield redis


@pytest.fixture
def setup_worker(setup_redis):
    worker = Worker(["default"], connection=setup_redis, name=worker_name)
    thread = threading.Thread(target=worker.work, daemon=True)
    thread.start()
    yield worker
    worker.teardown()


def test_get_workers(setup_worker):
    redis_url = "redis://redis:6379"

    redis_conn = Redis.from_url(redis_url)

    worker = Worker.count(connection=redis_conn)

    assert worker == 1


def test_convert_worker_data_to_json_dict():
    worker_data_1 = WorkerData(
        name="Worker 1",
        current_job="Job A",
        current_job_id="12345",
        successful_job_count=10,
        failed_job_count=2,
        queues=["Queue 1", "Queue 2"],
    )
    worker_data_2 = WorkerData(
        name="Worker 2",
        current_job="Job B",
        current_job_id="67890",
        successful_job_count=15,
        failed_job_count=3,
        queues=["Queue 2", "Queue 3"],
    )
    worker_data = [worker_data_1, worker_data_2]
    result_json = convert_worker_data_to_json_dict(worker_data)
    expected_json = [
        {
            "Worker 1": {
                "name": "Worker 1",
                "current_job": "Job A",
                "current_job_id": "12345",
                "successful_job_count": 10,
                "failed_job_count": 2,
                "queues": ["Queue 1", "Queue 2"],
            },
            "Worker 2": {
                "name": "Worker 2",
                "current_job": "Job B",
                "current_job_id": "67890",
                "successful_job_count": 15,
                "failed_job_count": 3,
                "queues": ["Queue 2", "Queue 3"],
            },
        }
    ]

    assert result_json == expected_json


def test_convert_workers_dict_to_list():
    input_data = [
        {
            "Worker 1": {
                "name": "Worker 1",
                "current_job": "Job A",
                "current_job_id": "12345",
                "successful_job_count": 10,
                "failed_job_count": 2,
                "queues": ["Queue 1", "Queue 2"],
            },
            "Worker 2": {
                "name": "Worker 2",
                "current_job": "Job B",
                "current_job_id": "67890",
                "successful_job_count": 15,
                "failed_job_count": 3,
                "queues": ["Queue 2", "Queue 3"],
            },
        }
    ]
    expected_data = [
        {
            "worker_name": "Worker 1",
            "current_job": "Job A",
            "current_job_id": "12345",
            "successful_job_count": 10,
            "failed_job_count": 2,
            "queue_name": ["Queue 1", "Queue 2"],
        },
        {
            "worker_name": "Worker 2",
            "current_job": "Job B",
            "current_job_id": "67890",
            "successful_job_count": 15,
            "failed_job_count": 3,
            "queue_name": ["Queue 2", "Queue 3"],
        },
    ]

    result_list = convert_workers_dict_to_list(input_data)

    assert result_list == expected_data
