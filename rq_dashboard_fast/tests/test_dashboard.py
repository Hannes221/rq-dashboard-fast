import threading
from random import randint

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis import Redis
from rq import Queue, Worker

from rq_dashboard_fast import RedisQueueDashboard

# RUN PYTEST IN DOCKER CONTAINER

worker_name = "test"
queue_name = "test_queue"


async def example_task() -> int:
    return randint(0, 100)


@pytest.fixture
def setup_redis():
    redis = Redis(port=6379, host="redis")
    yield redis


@pytest.fixture
def client():
    app = FastAPI()
    dashboard = RedisQueueDashboard(redis_url="redis://redis:6379", prefix="")

    app.mount("", dashboard)
    return TestClient(app)


@pytest.fixture
def create_queue(setup_redis):
    queue = Queue(connection=setup_redis, name=queue_name)
    return queue


@pytest.fixture
def add_task(create_queue):
    job = create_queue.enqueue(example_task)
    return job


@pytest.fixture
def setup_worker(setup_redis):
    worker = Worker(["default"], connection=setup_redis, name=worker_name)
    thread = threading.Thread(target=worker.work, daemon=True)
    thread.start()
    yield worker
    worker.teardown()


def test_add_job(client, add_task):
    job_id = add_task.id

    response = client.get("/job/" + job_id)
    assert job_id in response.text

    response_read_html = client.get("/jobs")
    assert response_read_html.status_code == 200
    assert job_id in response_read_html.text

    response_read_json = client.get("/jobs/json")
    assert response_read_json.status_code == 200
    assert job_id in response.text


def test_get_job_data(client, add_task):
    job_id = add_task.id

    response = client.get(f"/job/{job_id}")
    assert response.status_code == 200
    assert job_id in response.text


def test_get_jobs(client, add_task):
    job_id = add_task.id

    response = client.get("/jobs")
    assert response.status_code == 200
    assert job_id in response.text

    response = client.get("/jobs/json")
    assert response.status_code == 200
    assert job_id in response.text


def test_delete_job(client, add_task):
    job_id = add_task.id

    response_delete = client.delete(f"/job/{job_id}")
    assert response_delete.status_code == 200

    response_read_html_after_delete = client.get("/jobs")
    assert response_read_html_after_delete.status_code == 200
    assert job_id not in response_read_html_after_delete.text


def test_delete_jobs_in_queue(client, add_task):
    job_id = add_task.id

    response_delete = client.delete(f"/queues/{queue_name}")
    assert response_delete.status_code == 200

    response = client.get("/jobs/json")
    assert response.status_code == 200
    assert job_id not in response.text


def test_get_queue_json(client):
    response_read_json = client.get("/queues/json")
    assert response_read_json.status_code == 200
    assert any(queue["queue_name"] == queue_name for queue in response_read_json.json())


def test_get_queues(client):
    response = client.get("/queues")

    assert queue_name in response.text


def test_get_workers_json(client, setup_worker):
    response_read_json = client.get("/workers/json")
    assert response_read_json.status_code == 200

    assert len(response_read_json.json()) == 1
