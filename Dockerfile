FROM python:3.11

ENV POETRYVERSION=1.5.1

RUN pip install poetry==${POETRYVERSION}
RUN poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-interaction --no-ansi

WORKDIR /app

COPY ./rq_dashboard_fast /app/rq_dashboard_fast