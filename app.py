from fastapi import FastAPI
from rq import Queue, Worker, Connection
from routers import workers, jobs, queues, web
import redis

app = FastAPI()

app.include_router(workers.router)
app.include_router(jobs.router)
app.include_router(queues.router)
app.include_router(web.router)
