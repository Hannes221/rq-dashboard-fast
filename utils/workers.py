from pydantic import BaseModel
from rq import Worker
from utils.redis_conn import redis

class WorkerData(BaseModel):
    name: str
    current_job: str | None
    queues: list[str]

def get_workers() -> list[WorkerData]:
    workers = Worker.all(connection=redis)
    result = []
    
    for worker in workers:
        current_job = worker.get_current_job()
        if current_job is not None:
            result.append(WorkerData(name=worker.name, current_job=current_job.description, queues=worker.queue_names()))
        result.append(WorkerData(name=worker.name, current_job="Idle", queues=worker.queue_names()))
    
    return result