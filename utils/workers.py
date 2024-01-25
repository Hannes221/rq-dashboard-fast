from pydantic import BaseModel
from rq import Worker
from utils.redis_conn import redis

class WorkerData(BaseModel):
    name: str
    current_job: str
    queues: list[str]

def get_workers() -> list[WorkerData]:
    workers = Worker.all(connection=redis)
    result = []
    
    for worker in workers:
        result.append(WorkerData(name=worker.name, current_job=worker.get_current_job(), queues=worker.queue_names))
    
    return result