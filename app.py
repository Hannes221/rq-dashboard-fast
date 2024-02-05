import os
from fastapi import FastAPI
import uvicorn
from rq_dashboard_fast.rq_dashboard_fast import RedisQueueDashboard

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis")

dashboard = RedisQueueDashboard(redis_url=REDIS_URL, prefix="/rq")

app.mount("/rq", dashboard)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)