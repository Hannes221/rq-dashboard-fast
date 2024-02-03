from fastapi import FastAPI
from rq_dashboard_fast import RedisQueueDashboard

dashboard = RedisQueueDashboard("redis://localhost:6379/", prefix="/rq")


app = FastAPI()

app.mount("/rq", dashboard)