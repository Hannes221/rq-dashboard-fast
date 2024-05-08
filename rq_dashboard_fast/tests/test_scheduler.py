from datetime import datetime, timedelta

import pytest
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from ..utils.jobs import get_job_registrys


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


def test_scheduled_job(setup_redis, setup_queue, setup_scheduler):
    redis_url = "redis://redis:6379"
    job_name = "scheduled_test_job"

    scheduled_time = datetime.now() + timedelta(seconds=1000)
    job = setup_scheduler.enqueue_at(scheduled_time, example_task)

    job_registries = get_job_registrys(redis_url, state="scheduled")

    assert job_name in job_registries[2].scheduled[0].name
