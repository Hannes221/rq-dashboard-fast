from typing import List
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from rq.job import Job

class JobRegistryStats(BaseModel):
    queued: List[str]
    started: List[str]
    failed: List[str]
    deferred: List[str]
    finished: List[str]

def get_job_registry_stats():
    redis = Redis()
    queue = Queue(connection=redis)
    
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
            started_jobs.append(job.id)
        elif status == 'failed':
            failed_jobs.append(job.id)
        elif status == 'deferred':
            deferred_jobs.append(job.id)
        elif status == 'finished':
            finished_jobs.append(job.id)
        elif status == 'queued':
            queued_jobs.append(job.id)

    return JobRegistryStats(
        started=started_jobs,
        failed=failed_jobs,
        deferred=deferred_jobs,
        finished=finished_jobs,
        queued=queued_jobs
    )
