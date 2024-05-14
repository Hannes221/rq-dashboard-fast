from datetime import datetime, timedelta

import pytest
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from ..utils.jobs import get_job_registrys

# Fixture for setting up a Redis connection
@pytest.fixture
def setup_redis():
    redis = Redis(port=6379, host="redis")
    yield redis

# Fixture for setting up a Scheduler using the Redis connection
@pytest.fixture
def setup_scheduler(setup_redis):
    scheduler = Scheduler(connection=setup_redis)
    yield scheduler


# Fixture for setting up a Queue using the Redis connection
@pytest.fixture
def setup_queue(setup_redis):
    queue = Queue(connection=setup_redis)
    yield queue


def example_task():
    return "Hello World"

# Test function to verify the scheduling and visibility of a job in the registry
def test_scheduled_job(setup_redis, setup_queue, setup_scheduler):
    # Define the Redis URL for job registry retrieval
    redis_url = "redis://redis:6379"
    
    # Define a name for the job to be scheduled
    job_name = "scheduled_test_job"

    # Set a time in the future (1000 seconds later) to schedule the job
    scheduled_time = datetime.now() + timedelta(seconds=1000)
    
    # Enqueue the job at the scheduled time
    job = setup_scheduler.enqueue_at(scheduled_time, example_task)

    # Retrieve job registries to verify the job's presence
    job_registries = get_job_registrys(redis_url, state="scheduled")

    # Assert that the job name is in the retrieved scheduled job registry
    assert job_name in job_registries[2].scheduled[0].name
