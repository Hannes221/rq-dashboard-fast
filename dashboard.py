import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from utils.jobs import get_jobs
from utils.workers import get_workers
from utils.queues import delete_jobs_for_queue, get_job_registry_amount

class RedisQueueDashboard(FastAPI):
    def __init__(self, redis_url: str = "redis://localhost:6379", *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.mount("/static", StaticFiles(directory="static"), name="static")

        templates_directory = os.path.join(os.getcwd(), 'templates')
        self.templates = Jinja2Templates(directory=templates_directory)
        self.redis_url = redis_url 

        self.rq_dashboard_version = "1.0" 

        @self.get("/", response_class=HTMLResponse)
        async def get_home(request: Request):
            return self.templates.TemplateResponse(
                "base.html",
                {"request": request, "active_tab": "jobs",
                 "instance_list": [], "rq_dashboard_version": "1.0"}
            )

        @self.get("/workers", response_class=HTMLResponse)
        async def read_workers(request: Request):
            worker_data = get_workers(self.redis_url)

            active_tab = 'workers' 

            return self.templates.TemplateResponse(
                "workers.html",
                {"request": request, "worker_data": worker_data, "active_tab": active_tab,
                 "instance_list": [], "rq_dashboard_version": self.rq_dashboard_version}
            )

        @self.delete("/queues/{name}")
        def delete_jobs_in_queue(queue_name: str):
            deleted_ids = delete_jobs_for_queue(queue_name, self.redis_url)
            return deleted_ids

        @self.get("/queues", response_class=HTMLResponse)
        async def read_queues(request: Request):
            queue_data = get_job_registry_amount(self.redis_url)

            active_tab = 'queues' 

            return self.templates.TemplateResponse(
                "queues.html",
                {"request": request, "queue_data": queue_data, "active_tab": active_tab,
                 "instance_list": [], "rq_dashboard_version": self.rq_dashboard_version}
            )

        @self.get("/jobs", response_class=HTMLResponse)
        async def read_jobs(request: Request):
            job_data = get_jobs(self.redis_url)

            active_tab = 'jobs' 

            return self.templates.TemplateResponse(
                "jobs.html",
                {"request": request, "job_data": job_data, "active_tab": active_tab,
                 "instance_list": [], "rq_dashboard_version": self.rq_dashboard_version}
            )