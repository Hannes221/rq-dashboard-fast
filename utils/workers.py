from pydantic import BaseModel
from redis import Redis
from rq import Worker

class WorkerData(BaseModel):
    name: str
    current_job: str
    queues: list[str]

def get_workers(redis_url: str) -> list[WorkerData]:
    redis = Redis.from_url(redis_url)
    workers = Worker.all(connection=redis)
    result = []
    
    for worker in workers:
        result.append(WorkerData(name=worker.name, current_job=worker.get_current_job(), queues=worker.queue_names))
    
    return result