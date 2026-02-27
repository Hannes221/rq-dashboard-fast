import argparse
import os

import uvicorn
from fastapi import FastAPI

from rq_dashboard_fast import RedisQueueDashboard


def main():
    parser = argparse.ArgumentParser(description="RQ Dashboard FastAPI")
    parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL", "redis://localhost:6379"),
        help="Redis URL (default: $REDIS_URL or redis://localhost:6379)",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("FASTAPI_PORT", 8000)),
        help="Port to listen on (default: $FASTAPI_PORT or 8000)",
    )
    parser.add_argument(
        "--prefix",
        default="/rq",
        help="URL prefix for the dashboard (default: /rq)",
    )
    args = parser.parse_args()

    app = FastAPI()
    dashboard = RedisQueueDashboard(redis_url=args.redis_url, prefix=args.prefix)
    app.mount(args.prefix, dashboard)

    uvicorn.run(app, host=args.host, port=args.port)
