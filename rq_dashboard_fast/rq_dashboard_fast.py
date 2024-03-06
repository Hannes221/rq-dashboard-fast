import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from rq_dashboard_fast.utils.jobs import (
    JobDataDetailed,
    QueueJobRegistryStats,
    delete_job_id,
    get_job,
    get_jobs,
)
from rq_dashboard_fast.utils.queues import (
    QueueRegistryStats,
    delete_jobs_for_queue,
    get_job_registry_amount,
)
from rq_dashboard_fast.utils.workers import WorkerData, get_workers


class RedisQueueDashboard(FastAPI):
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        prefix: str = "/rq",
        *args,
        **kwargs
    ):
        super().__init__(root_path=prefix, *args, **kwargs)

        package_directory = Path(__file__).resolve().parent
        static_directory = package_directory / "static"

        self.mount("/static", StaticFiles(directory=static_directory), name="static")

        templates_directory = package_directory / "templates"
        self.templates = Jinja2Templates(directory=templates_directory)
        self.redis_url = redis_url

        self.rq_dashboard_version = "0.3.7"

        logger = logging.getLogger(__name__)

        @self.get("/", response_class=HTMLResponse)
        async def get_home(request: Request):
            try:
                return self.templates.TemplateResponse(
                    "base.html",
                    {
                        "request": request,
                        "active_tab": "jobs",
                        "prefix": prefix,
                        "rq_dashboard_version": self.rq_dashboard_version,
                    },
                )
            except Exception as e:
                logger.exception(
                    "An error occurred while loading the base template:", e
                )
                raise HTTPException(
                    "An error occurred while loading the base template:", e
                )

        @self.get("/workers", response_class=HTMLResponse)
        async def read_workers(request: Request):
            try:
                worker_data = get_workers(self.redis_url)

                active_tab = "workers"

                return self.templates.TemplateResponse(
                    "workers.html",
                    {
                        "request": request,
                        "worker_data": worker_data,
                        "active_tab": active_tab,
                        "prefix": prefix,
                        "rq_dashboard_version": self.rq_dashboard_version,
                    },
                )
            except Exception as e:
                logger.exception("An error occurred while reading workers:", e)
                raise HTTPException("An error occurred while reading workers:", e)

        @self.get("/workers/json", response_model=list[WorkerData])
        async def read_workers():
            try:
                worker_data = get_workers(self.redis_url)

                return worker_data
            except Exception as e:
                logger.exception(
                    "An error occurred while reading worker data in json:", e
                )
                raise HTTPException(
                    "An error occurred while reading worker data in json:", e
                )

        @self.delete("/queues/{queue_name}")
        def delete_jobs_in_queue(queue_name: str):
            try:
                deleted_ids = delete_jobs_for_queue(queue_name, self.redis_url)
                return deleted_ids
            except Exception as e:
                logger.exception("An error occurred while deleting jobs in queue:", e)
                raise HTTPException(
                    "An error occurred while deleting jobs in queue:", e
                )

        @self.get("/queues", response_class=HTMLResponse)
        async def read_queues(request: Request):
            try:
                queue_data = get_job_registry_amount(self.redis_url)

                active_tab = "queues"

                return self.templates.TemplateResponse(
                    "queues.html",
                    {
                        "request": request,
                        "queue_data": queue_data,
                        "active_tab": active_tab,
                        "prefix": prefix,
                        "rq_dashboard_version": self.rq_dashboard_version,
                    },
                )
            except Exception as e:
                logger.exception("An error occurred reading queues data template:", e)
                raise HTTPException(
                    "An error occurred reading queues data template:", e
                )

        @self.get("/queues/json", response_model=list[QueueRegistryStats])
        async def read_queues():
            try:
                queue_data = get_job_registry_amount(self.redis_url)

                return queue_data
            except Exception as e:
                logger.exception("An error occurred reading queues data json:", e)
                raise HTTPException("An error occurred reading queues data json:", e)

        @self.get("/jobs", response_class=HTMLResponse)
        async def read_jobs(
            request: Request,
            queue_name: str = Query("all"),
            state: str = Query("all"),
            page: str = Query(1),
        ):
            try:
                job_data = get_jobs(self.redis_url, queue_name, state)

                active_tab = "jobs"

                return self.templates.TemplateResponse(
                    "jobs.html",
                    {
                        "request": request,
                        "job_data": job_data,
                        "active_tab": active_tab,
                        "prefix": prefix,
                        "rq_dashboard_version": self.rq_dashboard_version,
                    },
                )
            except Exception as e:
                logger.exception("An error occurred reading jobs data template:", e)
                raise HTTPException("An error occurred reading jobs data template:", e)

        @self.get("/jobs/json", response_model=list[QueueJobRegistryStats])
        async def read_jobs(
            queue_name: str = Query("all"),
            state: str = Query("all"),
            page: str = Query("1"),
        ):
            try:
                job_data = get_jobs(self.redis_url, queue_name, state)

                return job_data
            except Exception as e:
                logger.exception("An error occurred reading jobs data json:", e)
                raise HTTPException("An error occurred reading jobs data json:", e)

        @self.get("/job/{job_id}", response_model=JobDataDetailed)
        async def get_job_data(job_id: str, request: Request):
            try:
                job = get_job(self.redis_url, job_id)

                active_tab = "job"

                return self.templates.TemplateResponse(
                    "job.html",
                    {
                        "request": request,
                        "job_data": job,
                        "active_tab": active_tab,
                        "prefix": prefix,
                        "rq_dashboard_version": self.rq_dashboard_version,
                    },
                )
            except Exception as e:
                logger.exception("An error occurred fetching a specific job:", e)
                raise HTTPException("An error occurred fetching a specific job:", e)

        @self.delete("/job/{job_id}")
        def delete_job(job_id: str):
            try:
                delete_job_id(self.redis_url, job_id=job_id)
            except Exception as e:
                logger.exception("An error occurred while deleting a job:", e)
                raise HTTPException("An error occurred while deleting a job:", e)
