import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from rq import Queue, Worker, Connection
import uvicorn
from routers import workers, jobs, queues, web
import redis

app = FastAPI()

templates_directory = os.path.join(os.getcwd(), 'templates')
templates = Jinja2Templates(directory=templates_directory)

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse(
        "base.html",
        {"request": request, "active_tab": "jobs",
         "instance_list": [], "rq_dashboard_version": "1.0"}
    )

app.include_router(workers.router)
app.include_router(jobs.router)
app.include_router(queues.router)
app.include_router(web.router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")