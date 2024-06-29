import threading
import time

import pytest
from redis import Connection, Redis
from rq import Queue, Worker

from ..utils.workers import get_workers, convert_worker_data_to_json, WorkerData
import json

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
def test_convert_worker_data_to_json():
    worker_data_1 = WorkerData(
        name='Worker 1',
        current_job='Job A',
        current_job_id='12345',
        successful_job_count=10,
        failed_job_count=2,
        queues=['Queue 1', 'Queue 2']
    )  
    worker_data_2 = WorkerData(
        name='Worker 2',
        current_job='Job B',
        current_job_id='67890',
        successful_job_count=15,
        failed_job_count=3,
        queues=['Queue 2', 'Queue 3']
    )
    worker_data = [worker_data_1, worker_data_2]
    result_json = convert_worker_data_to_json(worker_data)
    expected_json_string = """
    [
        {
            "Worker 1": {
                "name": "Worker 1",
                "current_job": "Job A",
                "current_job_id": "12345",
                "successful_job_count": 10,
                "failed_job_count": 2,
                "queues": ["Queue 1", "Queue 2"]
            },
            "Worker 2": {
                "name": "Worker 2",
                "current_job": "Job B",
                "current_job_id": "67890",
                "successful_job_count": 15,
                "failed_job_count": 3,
                "queues": ["Queue 2", "Queue 3"]
            }
        }
    ]
    """
    expected_result = json.loads(expected_json_string)
    actual_result = json.loads(result_json)
    
    assert actual_result == expected_result