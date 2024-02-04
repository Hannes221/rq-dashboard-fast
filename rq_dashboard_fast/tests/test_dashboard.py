import pytest
from fastapi.testclient import TestClient
from rq_dashboard_fast import RedisQueueDashboard
from rq import Queue
from redis import Redis
from random import randint
from fastapi import FastAPI
import time


# START REDIS ON PORT 8379 LOCALLY BEFORE RUNNING THIS

queue_name = "test_queue"

async def example_task() -> int:
    return randint(0, 100)

@pytest.fixture
def setup_redis():
    redis = Redis(port=8379)
    yield redis
    
@pytest.fixture
def client():
    app = FastAPI()
    dashboard = RedisQueueDashboard(redis_url="redis://localhost:8379", prefix="")

    app.mount("", dashboard)
    return TestClient(app)

@pytest.fixture
def create_queue(setup_redis):
    queue = Queue(connection=setup_redis, name="test_queue")
    return queue

@pytest.fixture
def add_task(create_queue):
    job = create_queue.enqueue(example_task)
    return job

def test_get_queue(client):
    response_read_html = client.get("/queues")
    assert response_read_html.status_code == 200
    assert queue_name in response_read_html.text

    response_read_json = client.get("/queues/json")
    assert response_read_json.status_code == 200
    assert any(queue["queue_name"] == queue_name for queue in response_read_json.json())

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