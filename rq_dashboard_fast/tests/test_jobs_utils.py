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
)


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
