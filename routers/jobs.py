from pydantic import BaseModel
from typing import List
from utils.redis_conn import queue, redis
from fastapi import APIRouter
from rq.registry import DeferredJobRegistry, FinishedJobRegistry, FailedJobRegistry, StartedJobRegistry, ScheduledJobRegistry, BaseRegistry

router = APIRouter()

class JobRegistryStats(BaseModel):
    started: List[str]
    failed: List[str]
    deferred: List[str]
    finished: List[str]
    scheduled: List[str]

@router.get("/jobs", response_model=JobRegistryStats)
async def get_jobs():
    deferred_jobs = DeferredJobRegistry(connection=redis).get_job_ids()
    finished_jobs = FinishedJobRegistry(connection=redis).get_job_ids()
    failed_jobs = FailedJobRegistry(connection=redis).get_job_ids()
    started_jobs = StartedJobRegistry(connection=redis).get_job_ids()
    scheduled_jobs = ScheduledJobRegistry(queue=queue).get_job_ids()


    return JobRegistryStats(
        started=started_jobs,
        failed=failed_jobs,
        deferred=deferred_jobs,
        finished=finished_jobs,
        scheduled=scheduled_jobs
    )