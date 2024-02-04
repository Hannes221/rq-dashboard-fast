from fastapi import FastAPI
from rq_dashboard_fast.rq_dashboard_fast import RedisQueueDashboard

app = FastAPI()
dashboard = RedisQueueDashboard()

app.mount("/rq", dashboard)