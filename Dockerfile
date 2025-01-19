FROM python:3.12-slim

ENV POETRYVERSION=1.8.3 POETRY_VIRTUALENVS_CREATE=false PYTHONPATH=/app

RUN pip install poetry==${POETRYVERSION} --no-cache-dir

ARG INSTALL_DEV=false

COPY pyproject.toml README.md ./

# Use the build argument to conditionally install dev dependencies
RUN if [ "$INSTALL_DEV" = "true" ]; then \
        poetry install --no-interaction --no-ansi; \
    else \
        poetry install --no-interaction --no-ansi --without dev; \
    fi

COPY ./rq_dashboard_fast /app/rq_dashboard_fast
COPY app.py /app

WORKDIR /app