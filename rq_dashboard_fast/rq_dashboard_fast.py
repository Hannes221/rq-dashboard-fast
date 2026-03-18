import asyncio
import csv
import json
import logging
from io import BytesIO, StringIO
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.templating import Jinja2Templates
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers.python import Python2TracebackLexer
from starlette.staticfiles import StaticFiles

from rq_dashboard_fast.utils.auth import (
    COOKIE_NAME,
    CSRF_COOKIE_NAME,
    AuthConfig,
    TokenPermissions,
    generate_csrf_token,
    hash_token,
    queue_allowed,
    worker_visible,
)
from rq_dashboard_fast.utils.jobs import (
    JobDataDetailed,
    PaginatedJobResponse,
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

_MUTATION_METHODS = {"DELETE", "POST", "PUT", "PATCH"}


def _get_permissions(request: Request) -> TokenPermissions:
    return getattr(request.state, "permissions", TokenPermissions())


def _require_admin(permissions: TokenPermissions, queue_name: str):
    if permissions.access != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if not queue_allowed(queue_name, permissions.queues):
        raise HTTPException(status_code=403, detail="Access denied for this queue")


class RedisQueueDashboard(FastAPI):
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        prefix: str = "/rq",
        protocol: str | None = None,
        auth_config: str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(root_path=prefix, *args, **kwargs)

        package_directory = Path(__file__).resolve().parent
        static_directory = package_directory / "static"

        self.mount("/static", StaticFiles(directory=static_directory), name="static")

        templates_directory = package_directory / "templates"
        self.templates = Jinja2Templates(directory=templates_directory)
        self.redis_url = redis_url
        self.protocol = protocol
        self.auth = AuthConfig(auth_config)

        self.rq_dashboard_version = "0.8.0"

        logger = logging.getLogger(__name__)

        # --- Auth middleware ---
        @self.middleware("http")
        async def auth_middleware(request: Request, call_next):
            # Static assets always pass through
            if request.url.path.startswith(
                f"{request.scope.get('root_path', '')}/static"
            ):
                return await call_next(request)

            if not self.auth.enabled:
                request.state.permissions = TokenPermissions(
                    authenticated=True, queues=["*"], access="admin"
                )
                return await call_next(request)

            # Check for ?token= query param → set cookie and redirect
            token_param = request.query_params.get("token")
            if token_param:
                token_hash = hash_token(token_param)
                entry = self.auth.resolve_hash(token_hash)
                if entry:
                    # Build redirect URL without the token param
                    params = {
                        k: v for k, v in request.query_params.items() if k != "token"
                    }
                    redirect_path = str(request.url.path)
                    if params:
                        redirect_path = f"{redirect_path}?{urlencode(params)}"
                    response = RedirectResponse(url=redirect_path, status_code=302)
                    csrf = generate_csrf_token()
                    is_https = request.url.scheme == "https"
                    cookie_path = request.scope.get("root_path", "/") or "/"
                    response.set_cookie(
                        COOKIE_NAME,
                        token_hash,
                        httponly=True,
                        samesite="lax",
                        secure=is_https,
                        path=cookie_path,
                    )
                    response.set_cookie(
                        CSRF_COOKIE_NAME,
                        csrf,
                        httponly=True,
                        samesite="lax",
                        secure=is_https,
                        path=cookie_path,
                    )
                    return response
                # Invalid token — fall through to login page

            # Check cookie
            cookie_hash = request.cookies.get(COOKIE_NAME)
            if cookie_hash:
                entry = self.auth.resolve_hash(cookie_hash)
                if entry:
                    csrf = request.cookies.get(CSRF_COOKIE_NAME, "")

                    # CSRF check on mutation requests
                    if request.method in _MUTATION_METHODS:
                        csrf_header = request.headers.get("x-csrf-token", "")
                        if not csrf or csrf_header != csrf:
                            return JSONResponse(
                                {"detail": "CSRF token missing or invalid"},
                                status_code=403,
                            )

                    request.state.permissions = TokenPermissions(
                        authenticated=True,
                        queues=entry["queues"],
                        access=entry["access"],
                        title=entry.get("title"),
                        csrf_token=csrf,
                        allow_workers=entry.get("allow_workers", True),
                        allow_export=entry.get("allow_export", True),
                        hide_meta=entry.get("hide_meta", False),
                    )
                    return await call_next(request)

            # No valid auth — show login page
            login_path = request.scope.get("root_path", prefix) + "/login"
            if not request.url.path.endswith("/login"):
                return RedirectResponse(url=login_path, status_code=302)
            return await call_next(request)

        # --- Login page ---
        @self.get("/login", response_class=HTMLResponse)
        async def login_page(request: Request, error: str = Query(None)):
            return self.templates.TemplateResponse(
                "login.html",
                {"request": request, "prefix": prefix, "error": error},
            )

        # --- Template context helper ---
        def _ctx(request: Request, extra: dict) -> dict:
            perms = _get_permissions(request)
            protocol_val = self.protocol if self.protocol else request.url.scheme
            base = {
                "request": request,
                "prefix": prefix,
                "rq_dashboard_version": self.rq_dashboard_version,
                "protocol": protocol_val,
                "access": perms.access,
                "csrf_token": perms.csrf_token or "",
                "custom_title": perms.title,
                "auth_enabled": self.auth.enabled,
                "allow_workers": perms.allow_workers,
                "allow_export": perms.allow_export,
                "hide_meta": perms.hide_meta,
            }
            base.update(extra)
            return base

        @self.get("/", response_class=HTMLResponse)
        async def get_home(
            request: Request,
            queue_name: str = Query("all"),
            state: str = Query("all"),
            page: int = Query(1),
            per_page: int = Query(10),
        ):
            try:
                perms = _get_permissions(request)
                paginated = get_jobs(
                    self.redis_url,
                    queue_name,
                    state,
                    page=page,
                    per_page=per_page,
                    allowed_queues=perms.queues,
                )

                return self.templates.TemplateResponse(
                    "jobs.html",
                    _ctx(
                        request,
                        {
                            "job_data": paginated.data,
                            "page": paginated.page,
                            "per_page": paginated.per_page,
                            "total_pages": paginated.total_pages,
                            "total": paginated.total,
                            "active_tab": "jobs",
                        },
                    ),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception(
                    "An error occurred while loading the base template: %s", e
                )
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while loading the base template",
                )

        @self.get("/workers", response_class=HTMLResponse)
        async def read_workers(request: Request):
            try:
                perms = _get_permissions(request)
                if self.auth.enabled and not perms.allow_workers:
                    raise HTTPException(status_code=403, detail="Workers page disabled")
                worker_data = get_workers(self.redis_url)
                worker_data = [
                    w for w in worker_data if worker_visible(w.queues, perms.queues)
                ]

                return self.templates.TemplateResponse(
                    "workers.html",
                    _ctx(
                        request,
                        {
                            "worker_data": worker_data,
                            "active_tab": "workers",
                        },
                    ),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("An error occurred while reading workers: %s", e)
                raise HTTPException(
                    status_code=500, detail="An error occurred while reading workers"
                )

        @self.get("/workers/json", response_model=list[WorkerData])
        async def read_workers_json(request: Request):
            try:
                perms = _get_permissions(request)
                if self.auth.enabled and not perms.allow_workers:
                    raise HTTPException(status_code=403, detail="Workers page disabled")
                worker_data = get_workers(self.redis_url)
                worker_data = [
                    w for w in worker_data if worker_visible(w.queues, perms.queues)
                ]

                return worker_data
            except HTTPException:
                raise
            except Exception as e:
                logger.exception(
                    "An error occurred while reading worker data in json: %s", e
                )
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while reading worker data in json",
                )

        @self.delete("/queues/{queue_name}")
        def delete_jobs_in_queue(queue_name: str, request: Request):
            try:
                perms = _get_permissions(request)
                _require_admin(perms, queue_name)
                deleted_ids = delete_jobs_for_queue(queue_name, self.redis_url)
                return deleted_ids
            except HTTPException:
                raise
            except Exception as e:
                logger.exception(
                    "An error occurred while deleting jobs in queue: %s", e
                )
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while deleting jobs in queue",
                )

        @self.get("/queues", response_class=HTMLResponse)
        async def read_queues(request: Request):
            try:
                perms = _get_permissions(request)
                queue_data = get_job_registry_amount(
                    self.redis_url,
                    allowed_queues=perms.queues,
                )

                return self.templates.TemplateResponse(
                    "queues.html",
                    _ctx(
                        request,
                        {
                            "queue_data": queue_data,
                            "active_tab": "queues",
                        },
                    ),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception(
                    "An error occurred reading queues data template: %s", e
                )
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred reading queues data template",
                )

        @self.get("/queues/json", response_model=list[QueueRegistryStats])
        async def read_queues(request: Request):
            try:
                perms = _get_permissions(request)
                queue_data = get_job_registry_amount(
                    self.redis_url,
                    allowed_queues=perms.queues,
                )

                return queue_data
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("An error occurred reading queues data json: %s", e)
                raise HTTPException(
                    status_code=500, detail="An error occurred reading queues data json"
                )

        @self.get("/jobs", response_class=HTMLResponse)
        async def read_jobs(
            request: Request,
            queue_name: str = Query("all"),
            state: str = Query("all"),
            page: int = Query(1),
            per_page: int = Query(10),
        ):
            try:
                perms = _get_permissions(request)
                paginated = get_jobs(
                    self.redis_url,
                    queue_name,
                    state,
                    page=page,
                    per_page=per_page,
                    allowed_queues=perms.queues,
                )

                return self.templates.TemplateResponse(
                    "jobs.html",
                    _ctx(
                        request,
                        {
                            "job_data": paginated.data,
                            "page": paginated.page,
                            "per_page": paginated.per_page,
                            "total_pages": paginated.total_pages,
                            "total": paginated.total,
                            "active_tab": "jobs",
                        },
                    ),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("An error occurred reading jobs data template: %s", e)
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred reading jobs data template",
                )

        @self.get("/jobs/json", response_model=PaginatedJobResponse)
        async def read_jobs(
            request: Request,
            queue_name: str = Query("all"),
            state: str = Query("all"),
            page: int = Query(1),
            per_page: int = Query(10),
        ):
            try:
                perms = _get_permissions(request)
                return get_jobs(
                    self.redis_url,
                    queue_name,
                    state,
                    page=page,
                    per_page=per_page,
                    allowed_queues=perms.queues,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("An error occurred reading jobs data json: %s", e)
                raise HTTPException(
                    status_code=500, detail="An error occurred reading jobs data json"
                )

        @self.get("/job/{job_id}", response_model=JobDataDetailed)
        async def get_job_data(job_id: str, request: Request):
            try:
                perms = _get_permissions(request)
                job = get_job(self.redis_url, job_id)

                # Check queue access for the job
                if self.auth.enabled:
                    if not job.origin or not queue_allowed(job.origin, perms.queues):
                        raise HTTPException(
                            status_code=403, detail="Access denied for this job's queue"
                        )

                if job.exc_info:
                    css = HtmlFormatter().get_style_defs()
                    col_exc_info = highlight(
                        job.exc_info, Python2TracebackLexer(), HtmlFormatter()
                    )
                else:
                    css = None
                    col_exc_info = None

                # Pretty-print dict/list results as JSON
                result = job.result
                if isinstance(result, (dict, list)):
                    try:
                        result_display = json.dumps(result, indent=2, default=str)
                    except Exception:
                        result_display = str(result)
                else:
                    result_display = str(result) if result is not None else None

                return self.templates.TemplateResponse(
                    "job.html",
                    _ctx(
                        request,
                        {
                            "job_data": job,
                            "active_tab": "job",
                            "css": css,
                            "col_exc_info": col_exc_info,
                            "result_display": result_display,
                        },
                    ),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("An error occurred fetching a specific job: %s", e)
                raise HTTPException(
                    status_code=500, detail="An error occurred fetching a specific job"
                )

        @self.delete("/job/{job_id}")
        def delete_job(job_id: str, request: Request):
            try:
                perms = _get_permissions(request)
                # Fetch job to determine its queue
                job = get_job(self.redis_url, job_id)
                queue_name = job.origin if hasattr(job, "origin") and job.origin else ""
                _require_admin(perms, queue_name)
                delete_job_id(self.redis_url, job_id=job_id)
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("An error occurred while deleting a job: %s", e)
                raise HTTPException(
                    status_code=500, detail="An error occurred while deleting a job"
                )

        @self.post("/job/{job_id}/requeue")
        def requeue_job(job_id: str, request: Request):
            try:
                perms = _get_permissions(request)
                # Fetch job to determine its queue
                job = get_job(self.redis_url, job_id)
                queue_name = job.origin if hasattr(job, "origin") and job.origin else ""
                _require_admin(perms, queue_name)
                requeue_job_id(self.redis_url, job_id=job_id)
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("An error occurred while requeueing a job: %s", e)
                raise HTTPException(
                    status_code=500, detail="An error occurred while requeueing a job"
                )

        @self.get("/export", response_class=HTMLResponse)
        async def export(request: Request):
            try:
                perms = _get_permissions(request)
                if self.auth.enabled and not perms.allow_export:
                    raise HTTPException(status_code=403, detail="Export page disabled")
                return self.templates.TemplateResponse(
                    "export.html",
                    _ctx(request, {"active_tab": "export"}),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception(
                    "An error occurred reading export data template: %s", e
                )
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred reading export data template",
                )

        @self.get("/export/queues")
        def export_queues(request: Request):
            try:
                perms = _get_permissions(request)
                if self.auth.enabled and not perms.allow_export:
                    raise HTTPException(status_code=403, detail="Export page disabled")
                queue_data = get_job_registry_amount(
                    self.redis_url,
                    allowed_queues=perms.queues,
                )
                json_dict = convert_queue_data_to_json_dict(queue_data)
                queue_list = convert_queues_dict_to_list(json_dict)
                csv_data = export_to_csv(queue_list, "queue_data.csv")
                output = BytesIO(csv_data.encode())
                headers = {"Content-Disposition": "attachment; filename=queue_data.csv"}
                return StreamingResponse(
                    output, headers=headers, media_type="application/octet-stream"
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("An error occurred while exporting: %s", e)
                raise HTTPException(
                    status_code=500, detail="An error occurred while exporting"
                )

        @self.get("/export/workers")
        def export_workers(request: Request):
            try:
                perms = _get_permissions(request)
                if self.auth.enabled and not perms.allow_export:
                    raise HTTPException(status_code=403, detail="Export page disabled")
                if self.auth.enabled and not perms.allow_workers:
                    raise HTTPException(
                        status_code=403, detail="Workers export disabled"
                    )
                worker_data = get_workers(self.redis_url)
                worker_data = [
                    w for w in worker_data if worker_visible(w.queues, perms.queues)
                ]
                json_dict = convert_worker_data_to_json_dict(worker_data)
                df = convert_workers_dict_to_list(json_dict)
                csv_data = export_to_csv(df, "worker_data.csv")
                output = BytesIO(csv_data.encode())
                headers = {
                    "Content-Disposition": "attachment; filename=worker_data.csv"
                }
                return StreamingResponse(
                    output, headers=headers, media_type="application/octet-stream"
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("An error occurred while exporting: %s", e)
                raise HTTPException(
                    status_code=500, detail="An error occurred while exporting"
                )

        @self.get("/export/jobs")
        def export_jobs(request: Request):
            try:
                perms = _get_permissions(request)
                if self.auth.enabled and not perms.allow_export:
                    raise HTTPException(status_code=403, detail="Export page disabled")
                paginated = get_jobs(
                    self.redis_url,
                    "all",
                    "all",
                    page=1,
                    allowed_queues=perms.queues,
                )
                json_dict = convert_queue_job_registry_stats_to_json_dict(
                    paginated.data
                )
                df = convert_queue_job_registry_dict_to_list(json_dict)
                csv_data = export_to_csv(df, "jobs_data.csv")
                output = BytesIO(csv_data.encode())
                headers = {"Content-Disposition": "attachment; filename=jobs_data.csv"}
                return StreamingResponse(
                    output, headers=headers, media_type="application/octet-stream"
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("An error occurred while exporting: %s", e)
                raise HTTPException(
                    status_code=500, detail="An error occurred while exporting"
                )


def export_to_csv(data: list[dict], filename: str) -> str:
    if not data:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()
