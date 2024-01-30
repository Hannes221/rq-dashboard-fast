import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from starlette.staticfiles import StaticFiles
from utils.jobs import QueueJobRegistryStats, get_jobs, JobDataDetailed, get_job
from utils.workers import WorkerData, get_workers
from utils.queues import QueueRegistryStats, delete_jobs_for_queue, get_job_registry_amount

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
    worker_data = get_workers()
    
    active_tab = 'workers' 

    return templates.TemplateResponse(
        "workers.html",
        {"request": request, "worker_data": worker_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )

@app.get("/workers/json", response_model=list[WorkerData])
async def read_workers():
    worker_data = get_workers()
    
    return worker_data
    
@app.delete("/queues/{queue_name}")
def delete_jobs_in_queue(queue_name: str):
    deleted_ids = delete_jobs_for_queue(queue_name)
    return deleted_ids
    

@app.get("/queues", response_class=HTMLResponse)
async def read_queues(request: Request):
    queue_data = get_job_registry_amount()

    active_tab = 'queues' 

    return templates.TemplateResponse(
        "queues.html",
        {"request": request, "queue_data": queue_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )
    
@app.get("/queues/json", response_model=list[QueueRegistryStats])
async def read_queues():
    queue_data = get_job_registry_amount()

    return queue_data
    

@app.get("/jobs", response_class=HTMLResponse)
async def read_jobs(request: Request):
    job_data = get_jobs()

    active_tab = 'jobs' 

    return templates.TemplateResponse(
        "jobs.html",
        {"request": request, "job_data": job_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )
    
@app.get("/jobs/json", response_model=list[QueueJobRegistryStats])
async def read_jobs():
    job_data = get_jobs()

    return job_data
    
@app.get("/job/{job_id}", response_model=JobDataDetailed)
async def get_job_data(job_id: str, request: Request):
    job = get_job(job_id)
    
    active_tab = "job"
    
    return templates.TemplateResponse(
        "job.html",
        {"request": request, "job_data": job, "active_tab": active_tab, 
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")