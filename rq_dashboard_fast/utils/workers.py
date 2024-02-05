from pydantic import BaseModel
from redis import Redis
from rq import Worker

class WorkerData(BaseModel):
    name: str
    current_job: str | None
    queues: list[str]

def get_workers(redis_url: str) -> list[WorkerData]:
    redis = Redis.from_url(redis_url)
    workers = Worker.all(connection=redis)
    result = []
    
    for worker in workers:
        current_job = worker.get_current_job()
        if current_job is not None:
            result.append(WorkerData(name=worker.name, current_job=current_job.description, queues=worker.queue_names()))
        else:
            result.append(WorkerData(name=worker.name, current_job="Idle", queues=worker.queue_names()))
    
    return result