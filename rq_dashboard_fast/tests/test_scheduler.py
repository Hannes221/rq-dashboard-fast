from datetime import datetime, timedelta

import pytest
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from ..utils.jobs import get_job_registrys

queue_name = "testqueue6"


def example_task() -> str:
    return ""


@pytest.fixture
def setup_redis():
    redis = Redis(port=6379, host="redis")
    yield redis


@pytest.fixture
def create_queue(setup_redis):
    queue = Queue(connection=setup_redis, name=queue_name)
    yield queue


@pytest.fixture
def setup_scheduler(setup_redis, create_queue):
    scheduler = Scheduler(connection=setup_redis, queue_name=queue_name)
    yield scheduler


@pytest.fixture
def add_task(setup_scheduler):
    scheduled_time = datetime.now() + timedelta(seconds=1000)
    job = setup_scheduler.enqueue_at(scheduled_time=scheduled_time, func=example_task)
    return job


def test_scheduled_job(setup_scheduler):
    redis_url = "redis://redis:6379"

    job_registries = get_job_registrys(redis_url, state="scheduled")

    assert any(
        "rq_dashboard_fast.tests.test_scheduler.example_task()" == job.name
        for registry in job_registries
        for job in registry.scheduled
    )
