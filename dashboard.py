import os
from fastapi import FastAPI, Request, middleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from utils import workers
from starlette.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from utils import jobs, queues

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates_directory = os.path.join(os.getcwd(), 'templates')
templates = Jinja2Templates(directory=templates_directory)

rq_dashboard_version = "1.0" 

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse(
        "base.html",
        {"request": request, "active_tab": "jobs",
         "instance_list": [], "rq_dashboard_version": "1.0"}
    )
    
@app.get("/workers", response_class=HTMLResponse)
async def read_workers(request: Request):
    worker_data = workers.get_workers()
    
    active_tab = 'workers' 

    return templates.TemplateResponse(
        "workers.html",
        {"request": request, "worker_data": worker_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )
    
@app.delete("/queues/{name}")
def delete_jobs_in_queue(queue_name: str):
    deleted_ids = queues.delete_jobs_for_queue(queue_name)
    return deleted_ids
    
@app.get("/queues/{name}", response_class=HTMLResponse)
async def read_queues(request: Request, name: str):
    queue_data = queues.get_job_registry_stats_for_queue(name)

    active_tab = 'queues' 

    return templates.TemplateResponse(
        "queues.html",
        {"request": request, "queue_data": queue_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )

@app.get("/queues", response_class=HTMLResponse)
async def read_queues(request: Request):
    queue_data = queues.get_queues()

    active_tab = 'queues' 

    return templates.TemplateResponse(
        "queues.html",
        {"request": request, "queue_data": queue_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )
    

@app.get("/jobs", response_class=HTMLResponse)
async def read_jobs(request: Request):
    job_data = jobs.get_jobs()

    active_tab = 'jobs' 

    return templates.TemplateResponse(
        "jobs.html",
        {"request": request, "job_data": job_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )