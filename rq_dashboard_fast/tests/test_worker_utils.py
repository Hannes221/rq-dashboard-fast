import threading
import time

import pytest
from redis import Connection, Redis
from rq import Queue, Worker

from ..utils.workers import get_workers

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
