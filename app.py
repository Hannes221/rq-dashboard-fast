import os
from fastapi import FastAPI
from rq_dashboard_fast.rq_dashboard_fast import RedisQueueDashboard

app = FastAPI()

dashboard = RedisQueueDashboard(redis_url="redis://redis:6379", prefix="/rq")

app.mount("/rq", dashboard)