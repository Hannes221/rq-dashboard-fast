import csv
import logging
from collections.abc import Callable
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, TypeVar

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers.python import Python2TracebackLexer
from starlette.staticfiles import StaticFiles

from rq_dashboard_fast.utils.jobs import (
    JobDataDetailed,
    QueueJobRegistryStats,
    convert_queue_job_registry_dict_to_list,
    convert_queue_job_registry_stats_to_json_dict,
    delete_job_id,
    get_job,
    get_jobs,
    requeue_job_id,
)
from rq_dashboard_fast.utils.queues import (
    QueueRegistryStats,
    convert_queue_data_to_json_dict,
    convert_queues_dict_to_list,
    delete_jobs_for_queue,
    get_job_registry_amount,
)
from rq_dashboard_fast.utils.workers import (
    WorkerData,
    convert_worker_data_to_json_dict,
    convert_workers_dict_to_list,
    get_workers,
)

T = TypeVar("T")


class RedisQueueDashboard(FastAPI):
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        prefix: str = "/rq",
        protocol: str | None = None,
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
        self.protocol = protocol
        self.prefix = prefix
        self.rq_dashboard_version = "0.6.0"
        self.logger = logging.getLogger(__name__)

        @self.get("/", response_class=HTMLResponse)
        async def get_home(
            request: Request,
            queue_name: str = Query("all"),
            state: str = Query("all"),
            page: int = Query(1),
        ):
            return self._render_jobs_page(request, queue_name, state, page)

        @self.get("/workers", response_class=HTMLResponse)
        async def read_workers_page(request: Request):
            worker_data = self._execute_with_error_handling(
                "An error occurred while reading workers",
                lambda: get_workers(self.redis_url),
            )
            return self._render(
                "workers.html",
                request,
                "workers",
                worker_data=worker_data,
            )

        @self.get("/workers/json", response_model=list[WorkerData])
        async def read_workers_json():
            return self._execute_with_error_handling(
                "An error occurred while reading worker data in json",
                lambda: get_workers(self.redis_url),
            )

        @self.delete("/queues/{queue_name}")
        def delete_jobs_in_queue(queue_name: str):
            return self._execute_with_error_handling(
                "An error occurred while deleting jobs in queue",
                lambda: delete_jobs_for_queue(queue_name, self.redis_url),
            )

        @self.get("/queues", response_class=HTMLResponse)
        async def read_queues_page(request: Request):
            queue_data = self._execute_with_error_handling(
                "An error occurred reading queues data template",
                lambda: get_job_registry_amount(self.redis_url),
            )
            return self._render(
                "queues.html",
                request,
                "queues",
                queue_data=queue_data,
            )

        @self.get("/queues/json", response_model=list[QueueRegistryStats])
        async def read_queues_json():
            return self._execute_with_error_handling(
                "An error occurred reading queues data json",
                lambda: get_job_registry_amount(self.redis_url),
            )

        @self.get("/jobs", response_class=HTMLResponse)
        async def read_jobs_page(
            request: Request,
            queue_name: str = Query("all"),
            state: str = Query("all"),
            page: int = Query(1),
        ):
            return self._render_jobs_page(request, queue_name, state, page)

        @self.get("/jobs/json", response_model=list[QueueJobRegistryStats])
        async def read_jobs_json(
            queue_name: str = Query("all"),
            state: str = Query("all"),
            page: int = Query(1),
        ):
            return self._execute_with_error_handling(
                "An error occurred while reading jobs data json",
                lambda: get_jobs(self.redis_url, queue_name, state, page=page),
            )

        @self.get("/job/{job_id}", response_model=JobDataDetailed)
        async def get_job_data(job_id: str, request: Request):
            job = self._execute_with_error_handling(
                "An error occurred fetching a specific job",
                lambda: get_job(self.redis_url, job_id),
            )

            if job.exc_info:
                css = HtmlFormatter().get_style_defs()
                col_exc_info = highlight(
                    job.exc_info, Python2TracebackLexer(), HtmlFormatter()
                )
            else:
                css = None
                col_exc_info = None

            return self._render(
                "job.html",
                request,
                "job",
                job_data=job,
                css=css,
                col_exc_info=col_exc_info,
            )

        @self.delete("/job/{job_id}")
        def delete_job(job_id: str):
            self._execute_with_error_handling(
                "An error occurred while deleting a job",
                lambda: delete_job_id(self.redis_url, job_id=job_id),
            )

        @self.post("/job/{job_id}/requeue")
        def requeue_job(job_id: str):
            self._execute_with_error_handling(
                "An error occurred while requeueing a job",
                lambda: requeue_job_id(self.redis_url, job_id=job_id),
            )

        @self.get("/export", response_class=HTMLResponse)
        async def export(request: Request):
            return self._render("export.html", request, "export")

        @self.get("/export/queues")
        def export_queues():
            queue_data = self._execute_with_error_handling(
                "An error occurred while exporting queues",
                lambda: get_job_registry_amount(self.redis_url),
            )
            json_dict = convert_queue_data_to_json_dict(queue_data)
            queue_list = convert_queues_dict_to_list(json_dict)
            return self._build_export_response(queue_list, "queue_data.csv")

        @self.get("/export/workers")
        def export_workers():
            worker_data = self._execute_with_error_handling(
                "An error occurred while exporting workers",
                lambda: get_workers(self.redis_url),
            )
            json_dict = convert_worker_data_to_json_dict(worker_data)
            workers_list = convert_workers_dict_to_list(json_dict)
            return self._build_export_response(workers_list, "worker_data.csv")

        @self.get("/export/jobs")
        def export_jobs():
            jobs_data = self._execute_with_error_handling(
                "An error occurred while exporting jobs",
                lambda: get_jobs(self.redis_url, "all", "all", page=1),
            )
            json_dict = convert_queue_job_registry_stats_to_json_dict(jobs_data)
            jobs_list = convert_queue_job_registry_dict_to_list(json_dict)
            return self._build_export_response(jobs_list, "jobs_data.csv")

    def _render_jobs_page(
        self,
        request: Request,
        queue_name: str,
        state: str,
        page: int,
    ) -> HTMLResponse:
        job_data = self._execute_with_error_handling(
            "An error occurred while reading jobs data template",
            lambda: get_jobs(self.redis_url, queue_name, state, page=page),
        )
        return self._render(
            "jobs.html",
            request,
            "jobs",
            job_data=job_data,
        )

    def _execute_with_error_handling(
        self, detail: str, func: Callable[[], T]
    ) -> T:
        try:
            return func()
        except Exception as exc:  # pragma: no cover - logged for visibility
            self.logger.exception(detail, exc_info=exc)
            raise HTTPException(status_code=500, detail=detail) from exc

    def _render(
        self,
        template_name: str,
        request: Request,
        active_tab: str,
        **context: Any,
    ) -> HTMLResponse:
        template_context = {
            **self._base_context(request, active_tab),
            **context,
        }
        return self.templates.TemplateResponse(template_name, template_context)

    def _base_context(self, request: Request, active_tab: str) -> dict[str, Any]:
        return {
            "request": request,
            "active_tab": active_tab,
            "prefix": self.prefix,
            "rq_dashboard_version": self.rq_dashboard_version,
            "protocol": self.protocol if self.protocol else request.url.scheme,
        }

    def _build_export_response(
        self,
        data: list[dict],
        filename: str,
    ) -> StreamingResponse:
        csv_data = export_to_csv(data, filename)
        output = BytesIO(csv_data.encode())
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return StreamingResponse(
            output,
            headers=headers,
            media_type="application/octet-stream",
        )


def export_to_csv(data: list[dict], filename: str) -> str:
    if not data:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()
