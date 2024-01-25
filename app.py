from fastapi import FastAPI
import uvicorn
from dashboard import app as rq_dashboard_fast_router

app = FastAPI()

app.mount("", rq_dashboard_fast_router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")