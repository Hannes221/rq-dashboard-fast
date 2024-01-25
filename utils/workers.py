from pydantic import BaseModel
from rq import Worker
from utils.redis_conn import redis

class WorkerData(BaseModel):
    name: str
    current_job: str
    queues: str

def get_workers() -> list[WorkerData]:
    workers = Worker.all(connection=redis)
    result = []
    
    for worker in workers:
        result.append(WorkerData(worker.name, worker.get_current_job(), worker.queue_names))
    
    return result