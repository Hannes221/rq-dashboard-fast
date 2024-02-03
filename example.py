from fastapi import FastAPI
from rq_dashboard_fast import RedisQueueDashboard

app = FastAPI()
dashboard = RedisQueueDashboard("redis://localhost:6379", "/rq")

app.mount("/rq", dashboard)