import os

import uvicorn
from fastapi import FastAPI

from rq_dashboard_fast.rq_dashboard_fast import RedisQueueDashboard

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
PORT = int(os.getenv("FASTAPI_PORT", 8000))

dashboard = RedisQueueDashboard(redis_url=REDIS_URL, prefix="/rq")

app.mount("/rq", dashboard)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
