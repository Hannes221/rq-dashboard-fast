import pytest
from datetime import datetime, timedelta
from rq_scheduler import Scheduler

from ..utils import get_job_registrys

@pytest.fixture
def setup_redis():
    redis = Redis(port=6379, host="redis")
    yield redis

@pytest.fixture
def setup_scheduler(setup_redis):
    scheduler = Scheduler(connection=setup_redis)
    yield scheduler

def test_scheduled_job_visibility(setup_redis, setup_scheduler):
    redis_url = "redis://redis:6379"
    job_name = "scheduled_test_job"

    scheduled_time = datetime.now() + timedelta(seconds=10)
    job = setup_scheduler.enqueue_at(scheduled_time, example_task, description=job_name)

    job_registries = get_job_registrys(redis_url, state="scheduled")

    assert any(
        job_data.name == job_name and job_data.id == job.id
        for queue_job in job_registries for job_data in queue_job.scheduled
    ), "Scheduled job not found in the registry"