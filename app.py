import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from rq import Queue, Worker, Connection
import uvicorn
from routers import workers, jobs, queues
import redis
from starlette.staticfiles import StaticFiles

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
    worker_data = await workers.get_workers()
    
    active_tab = 'workers' 

    return templates.TemplateResponse(
        "workers.html",
        {"request": request, "worker_data": worker_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )

@app.get("/queues", response_class=HTMLResponse)
async def read_queues(request: Request):
    queue_data = await queues.get_queues()

    active_tab = 'queues' 

    return templates.TemplateResponse(
        "queues.html",
        {"request": request, "queue_data": queue_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )

@app.get("/jobs", response_class=HTMLResponse)
async def read_jobs(request: Request):
    job_data = await jobs.get_jobs()

    active_tab = 'jobs' 

    return templates.TemplateResponse(
        "jobs.html",
        {"request": request, "job_data": job_data, "active_tab": active_tab,
         "instance_list": [], "rq_dashboard_version": rq_dashboard_version}
    )


app.include_router(workers.router)
app.include_router(jobs.router)
app.include_router(queues.router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")