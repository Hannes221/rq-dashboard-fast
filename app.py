import os
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from utils.jobs import QueueJobRegistryStats, get_jobs, JobDataDetailed, get_job, delete_job_id
from utils.workers import WorkerData, get_workers
from utils.queues import QueueRegistryStats, delete_jobs_for_queue, get_job_registry_amount

class RedisQueueDashboard(FastAPI):
    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "/rq", *args, **kwargs):
        super().__init__(root_path=prefix, *args, **kwargs)
        
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
                 "instance_list": [], "prefix": prefix, "rq_dashboard_version": self.rq_dashboard_version}
            )

        @self.get("/workers", response_class=HTMLResponse)
        async def read_workers(request: Request):
            worker_data = get_workers(self.redis_url)

            active_tab = 'workers' 

            return self.templates.TemplateResponse(
                "workers.html",
                {"request": request, "worker_data": worker_data, "active_tab": active_tab,
                "instance_list": [], "prefix": prefix, "rq_dashboard_version": self.rq_dashboard_version}
            )
            
        @self.get("/workers/json", response_model=list[WorkerData])
        async def read_workers():
            worker_data = get_workers(self.redis_url)
            
            return worker_data
    
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
                "instance_list": [], "prefix": prefix, "rq_dashboard_version": self.rq_dashboard_version}
            )
            
        @self.get("/queues/json", response_model=list[QueueRegistryStats])
        async def read_queues():
            queue_data = get_job_registry_amount(self.redis_url)

            return queue_data
    

        @self.get("/jobs", response_class=HTMLResponse)
        async def read_jobs(request: Request, queue_name: str = Query("all"), state: str = Query("all")):
            job_data = get_jobs(self.redis_url, queue_name, state)

            active_tab = 'jobs' 

            return self.templates.TemplateResponse(
                "jobs.html",
                {"request": request, "job_data": job_data, "active_tab": active_tab,
                "instance_list": [], "prefix": prefix, "rq_dashboard_version": self.rq_dashboard_version}
            )

        @self.get("/jobs/json", response_model=list[QueueJobRegistryStats])
        async def read_jobs(queue_name: str = Query(None), state: str = Query(None)):
            job_data = get_jobs(self.redis_url, queue_name, state)

            return job_data

            
        @self.get("/job/{job_id}", response_model=JobDataDetailed)
        async def get_job_data(job_id: str, request: Request):
            job = get_job(job_id)
            
            active_tab = "job"
            
            return self.templates.TemplateResponse(
                "job.html",
                {"request": request, "job_data": job, "active_tab": active_tab, 
                "instance_list": [], "prefix": prefix, "rq_dashboard_version": self.rq_dashboard_version}
            )
            
        @self.delete("/job/{job_id}")
        def delete_job(job_id: str):
            delete_job_id(job_id=job_id)
