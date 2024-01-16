from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from utils.redis_conn import queue
from routers import jobs, queues, workers

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/workers", response_class=HTMLResponse)
async def read_workers(request: Request):
    worker_data = workers.get_workers()
    return templates.TemplateResponse("workers.html", {"request": request, "worker_data": worker_data})

@router.get("/queues", response_class=HTMLResponse)
async def read_queues(request: Request):
    queue_data = queues.get_queues()
    return templates.TemplateResponse("queues.html", {"request": request, "queue_data": queue_data})

@router.get("/jobs", response_class=HTMLResponse)
async def read_jobs(request: Request):
    job_data = jobs.get_jobs()
    return templates.TemplateResponse("jobs.html", {"request": request, "job_data": job_data})
