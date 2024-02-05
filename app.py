import os
from fastapi import FastAPI
from rq_dashboard_fast import RedisQueueDashboard

app = FastAPI()

redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
print(f"Connecting to Redis using URL: {redis_url}")
dashboard = RedisQueueDashboard(redis_url=redis_url)

app.mount("/rq", dashboard)