import pytest
from redis import Redis
from rq import Queue
import json
from ..utils.queues import delete_jobs_for_queue, get_job_registry_amount, get_queues, convert_queue_data_to_json, QueueRegistryStats


@pytest.fixture
def setup_redis():
    redis = Redis(port=6379, host="redis")
    yield redis


def example_task():
    return "Hello World"


def test_get_queues(setup_redis):
    # Set up test data
    redis_url = "redis://redis:6379"
    queue_name = "test_queue"
    queue = Queue(connection=setup_redis, name=queue_name)

    queues = get_queues(redis_url)

    assert queue in queues


def test_get_job_registry_amount(setup_redis):
    redis_url = "redis://redis:6379"
    queue_name = "test_queue"
    queue = Queue(connection=setup_redis, name=queue_name)
    queue.enqueue(example_task)

    registry_stats = get_job_registry_amount(redis_url)

    assert any(
        stat.queued == 1 and stat.queue_name == queue_name for stat in registry_stats
    )


def test_delete_jobs_for_queue(setup_redis):
    redis_url = "redis://redis:6379"
    queue_name = "test_queue3"
    queue = Queue(connection=setup_redis, name=queue_name)
    queue.enqueue(example_task)

    registry_stats = get_job_registry_amount(redis_url)

    assert any(
        stat.queued == 1 and stat.queue_name == queue_name for stat in registry_stats
    )

    delete_jobs_for_queue(queue_name, redis_url)

    registry_stats = get_job_registry_amount(redis_url)

    assert any(
        stat.queued == 0 and stat.queue_name == queue_name for stat in registry_stats
    )
    
def test_convert_queue_data_to_json():
    queue_stats_1 = QueueRegistryStats(
        queue_name='Queue 1',
        queued=10,
        started=5,
        failed=2,
        deferred=3,
        finished=20
    )
    queue_stats_2 = QueueRegistryStats(
        queue_name='Queue 2',
        queued=15,
        started=8,
        failed=1,
        deferred=0,
        finished=25
    )
    queue_data = [queue_stats_1, queue_stats_2]
    result_json = convert_queue_data_to_json(queue_data)
    expected_json_string = """
    [
        {
            "Queue 1": {
                "queued": 10,
                "started": 5,
                "failed": 2,
                "deferred": 3,
                "finished": 20
            },
            "Queue 2": {
                "queued": 15,
                "started": 8,
                "failed": 1,
                "deferred": 0,
                "finished": 25
            }
        }
    ]
    """
    expected_result = json.loads(expected_json_string)
    actual_result = json.loads(result_json)
    
    assert actual_result == expected_result
