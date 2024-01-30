from pydantic import BaseModel
from redis import Redis
from utils.redis_conn import redis
from rq import Queue
from rq.job import Job


class QueueRegistryStats(BaseModel):
    queue_name: str
    queued: int
    started: int
    failed: int
    deferred: int
    finished: int

def get_queues() -> list[Queue]:
    queues = Queue.all(connection=Redis())
    
    return queues
    

def get_job_registry_amount() -> list[QueueRegistryStats]:
    queues = get_queues()
    result = []
    for queue in queues:
        jobs = queue.get_job_ids()
        
        jobs_fetched = Job.fetch_many(jobs, connection=redis)
        
        started_jobs = 0
        failed_jobs = 0
        deferred_jobs = 0
        finished_jobs = 0
        queued_jobs = 0

        for job in jobs_fetched:
            status = job.get_status()
            if status == 'started':
                started_jobs += 1
            elif status == 'failed':
                failed_jobs += 1
            elif status == 'deferred':
                deferred_jobs += 1
            elif status == 'finished':
                finished_jobs += 1
            elif status == 'queued':
                queued_jobs += 1
                
        result.append(QueueRegistryStats(queue_name=queue.name, queued=queued_jobs, started=started_jobs, failed=failed_jobs, deferred=deferred_jobs, finished=finished_jobs))
    return result

def delete_jobs_for_queue(queue_name) -> list[str]:
    queue = Queue(queue_name, connection=Redis())
    
    result = queue.empty()
        
    return result