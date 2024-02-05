import os
from fastapi import FastAPI
from rq_dashboard_fast.rq_dashboard_fast import RedisQueueDashboard

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis")

dashboard = RedisQueueDashboard(redis_url=REDIS_URL, prefix="/rq")

app.mount("/rq", dashboard)