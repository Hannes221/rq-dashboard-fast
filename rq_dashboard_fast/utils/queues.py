from pydantic import BaseModel
from redis import Redis
from rq import Queue


class QueueRegistryStats(BaseModel):
    queue_name: str
    queued: int
    started: int
    failed: int
    deferred: int
    finished: int

def get_queues(redis_url: str) -> list[Queue]:
    redis = Redis.from_url(redis_url)
    
    queues = Queue.all(connection=redis)
    
    return queues
    

def get_job_registry_amount(redis_url: str) -> list[QueueRegistryStats]:
    queues = get_queues(redis_url)
    result = []
    for queue in queues:
        finished_jobs = len(queue.finished_job_registry.get_job_ids())      
        started_jobs = len(queue.started_job_registry.get_job_ids()) 
        failed_jobs = len(queue.failed_job_registry.get_job_ids()) 
        deferred_jobs = len(queue.deferred_job_registry.get_job_ids()) 
        queued_jobs = len(queue.get_job_ids()) 
                
        result.append(QueueRegistryStats(queue_name=queue.name, queued=queued_jobs, started=started_jobs, failed=failed_jobs, deferred=deferred_jobs, finished=finished_jobs))
    return result

def delete_jobs_for_queue(queue_name, redis_url) -> list[str]:
    redis = Redis.from_url(redis_url)
    
    queue = Queue(queue_name, connection=redis)
    
    result = queue.empty()
        
    return result