from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from utils.redis_conn import queue
from routers import jobs, queues, workers

import os

router = APIRouter()

templates_directory = os.path.join(os.getcwd(), 'templates')

templates = Jinja2Templates(directory=templates_directory)

rq_dashboard_version = "1.0" 


@router.get("/workers", response_class=HTMLResponse)
async def read_workers(request: Request):
    worker_data = await workers.get_workers()
    
    active_tab = 'workers' 

    return templates.TemplateResponse(
        "workers.html",
        {"request": request, "worker_data": worker_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )

@router.get("/queues", response_class=HTMLResponse)
async def read_queues(request: Request):
    queue_data = await queues.get_queues()

    active_tab = 'queues' 

    return templates.TemplateResponse(
        "queues.html",
        {"request": request, "queue_data": queue_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )

@router.get("/jobs", response_class=HTMLResponse)
async def read_jobs(request: Request):
    job_data = await jobs.get_jobs()

    active_tab = 'jobs' 

    return templates.TemplateResponse(
        "jobs.html",
        {"request": request, "job_data": job_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )
