from fastapi import FastAPI
from dashboard import RedisQueueDashboard


dashboard = RedisQueueDashboard("redis://redis:6379/")


app = FastAPI()

app.mount("/rq", dashboard)