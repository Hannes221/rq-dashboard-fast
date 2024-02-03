from fastapi import FastAPI
from dashboard import RedisQueueDashboard


app = FastAPI()

dashboard = RedisQueueDashboard()

app.mount("/rq", dashboard)