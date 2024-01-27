from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from redis import Redis
from rq.job import Job
from rq import Queue

from utils.queues import get_queues

router = APIRouter()
    
class JobData(BaseModel):
    id: str
    name: str
    created_at: datetime

class QueueJobRegistryStats(BaseModel):
    queue_name: str
    queued: List[JobData]
    started: List[JobData]
    failed: List[JobData]
    deferred: List[JobData]
    finished: List[JobData]

def get_job_registrys(redis_url: str):
    redis = Redis.from_url(redis_url)
    
    queues = get_queues(redis_url)
    result = []
    for queue in queues:
        jobs = queue.get_job_ids()
        
        jobs_fetched = Job.fetch_many(jobs, connection=redis)
        
        started_jobs = []
        failed_jobs = []
        deferred_jobs = []
        finished_jobs = []
        queued_jobs = []

        for job in jobs_fetched:
            status = job.get_status()
            if status == 'started':
                started_jobs.append(JobData(id=job.id, name=job.description, created_at=job.created_at))
            elif status == 'failed':
                failed_jobs.append(JobData(id=job.id, name=job.description, created_at=job.created_at))
            elif status == 'deferred':
                deferred_jobs.append(JobData(id=job.id, name=job.description, created_at=job.created_at))
            elif status == 'finished':
                finished_jobs.append(JobData(id=job.id, name=job.description, created_at=job.created_at))
            elif status == 'queued':
                queued_jobs.append(JobData(id=job.id, name=job.description, created_at=job.created_at))
        result.append(QueueJobRegistryStats(queue_name=queue.name, queued=queued_jobs, started=started_jobs, failed=failed_jobs, deferred=deferred_jobs, finished=finished_jobs))
                
    return result

def get_jobs(redis_url: str) -> list[QueueJobRegistryStats]:
    try:
        job_stats = get_job_registrys(redis_url)
        return job_stats
    except Exception as e:
        # Handle specific exceptions if needed
        raise HTTPException(status_code=500, detail=str(e))
