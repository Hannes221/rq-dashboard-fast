from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from redis import Redis
from rq.job import Job

from utils.queues import get_queues

router = APIRouter()
    
    
class JobData(BaseModel):
    id: str
    name: str
    created_at: datetime
    
class JobDataDetailed(BaseModel):
    id: str
    name: str
    created_at: datetime
    enqueued_at: datetime | None
    ended_at: datetime | None
    result: Any
    exc_info: str | None
    meta: dict

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
        jobs.extend(queue.finished_job_registry.get_job_ids())
        jobs.extend(queue.failed_job_registry.get_job_ids())
        jobs.extend(queue.started_job_registry.get_job_ids())
        jobs.extend(queue.deferred_job_registry.get_job_ids())
        
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

def get_job(job_id: str) -> JobDataDetailed:
    job = Job.fetch(job_id, connection=Redis())

    return JobDataDetailed(id=job.id, name=job.description, created_at=job.created_at, enqueued_at=job.enqueued_at, ended_at=job.ended_at, result=job.result, exc_info=job.exc_info, meta=job.meta)

def delete_job_id(job_id: str):
    job = Job.fetch(job_id, connection=Redis())
    if job:
        job.delete()
