from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from utils.job_registries import get_job_registry_stats

router = APIRouter()

class JobRegistryStats(BaseModel):
    started: List[str]
    failed: List[str]
    deferred: List[str]
    finished: List[str]

@router.get("/task", response_class=JSONResponse)
def get_jobs():
    try:
        job_stats = get_job_registry_stats()
        return job_stats
    except Exception as e:
        # Handle specific exceptions if needed
        raise HTTPException(status_code=500, detail=str(e))
