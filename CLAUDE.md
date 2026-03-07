# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

rq-dashboard-fast is a FastAPI-based web dashboard for monitoring Redis Queue (RQ) jobs, queues, and workers. It's distributed as a Python package on PyPI and as Docker images on Docker Hub / GHCR.

## Commands

### Development
```bash
poetry install                    # Install all dependencies (including dev)
docker compose up                 # Run dashboard + Redis locally (mounts source for live reload)
poetry run python app.py          # Run manually (requires Redis at REDIS_URL)
```

### Frontend CSS (UnoCSS)
```bash
npm install                       # Install UnoCSS CLI (first time only)
npm run dev:css                   # Watch mode — rebuilds on template changes
npm run build:css                 # One-off production build
```

UnoCSS config is in `uno.config.ts`. It scans `rq_dashboard_fast/templates/**/*.html` and outputs to `rq_dashboard_fast/static/css/uno.css`. The generated file is committed — no Node.js needed at runtime. After changing templates or config, run `npm run build:css` and commit the result. Badge classes used in JS via dynamic construction (`'badge-' + state`) are in the `safelist` array.

### Testing
Tests require a Redis instance. The standard approach uses Docker:
```bash
docker compose build --build-arg INSTALL_DEV=true
docker compose up -d
docker exec rq-dashboard-fast-dashboard-1 pytest
```
Or locally if Redis is available: `poetry run pytest`

Tests live in `rq_dashboard_fast/tests/` and connect to Redis at `redis://redis:6379` (hostname `redis` from docker-compose).

### Code Formatting & Linting
```bash
poetry run pre-commit run --all-files   # Run all pre-commit hooks
poetry run black .                       # Format code
poetry run isort .                       # Sort imports
poetry run flake8                        # Lint
```

Pre-commit hooks enforce `black` and `isort` (configured with black profile).

### Build & Publish
```bash
poetry build                     # Build package
docker build -t rq-dashboard-fast .
```

CI/CD runs on GitHub Actions (triggered by releases): test → build → publish to PyPI + Docker Hub/GHCR.

## Architecture

### Core Pattern: Mountable FastAPI Sub-application

`RedisQueueDashboard` (in `rq_dashboard_fast/rq_dashboard_fast.py`) extends `FastAPI` itself, so it's mounted as a sub-application on any existing FastAPI app:

```python
app = FastAPI()
dashboard = RedisQueueDashboard(redis_url="redis://localhost:6379", prefix="/rq")
app.mount("/rq", dashboard)
```

The `prefix` parameter and optional `protocol` parameter handle reverse proxy/path-prefix scenarios for correct URL generation in templates.

### Module Structure

- **`rq_dashboard_fast/rq_dashboard_fast.py`** — All HTTP routes and Pydantic response models. Routes return either Jinja2 HTML responses or JSON/CSV via `StreamingResponse`.
- **`rq_dashboard_fast/utils/`** — Data layer separated by domain:
  - `jobs.py` — Job fetching, filtering by queue/status, detail retrieval, delete, requeue
  - `queues.py` — Queue listing, job count aggregation by status, queue clearing
  - `workers.py` — Worker status and statistics
- **`rq_dashboard_fast/templates/`** — Jinja2 HTML templates for the dashboard UI
- **`rq_dashboard_fast/static/css/`** — CSS assets served via Starlette's StaticFiles
- **`app.py`** — Example/development entry point

### Environment Variables

- `REDIS_URL` — Redis connection string (default: `redis://localhost:6379`)
- `FASTAPI_PORT` — Server port (default: `8000`)

### Key Details

- Python 3.10+ required; Dockerfile uses 3.12-slim
- CSV export uses Python's `csv` module (no pandas dependency)
- Tracebacks in job detail views use Pygments for syntax highlighting
- Pagination defaults to 10 items per page
- Multi-platform Docker builds: linux/amd64 and linux/arm64
