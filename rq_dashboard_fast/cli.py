import argparse
import os

import uvicorn
from fastapi import FastAPI

from rq_dashboard_fast import RedisQueueDashboard


def main():
    parser = argparse.ArgumentParser(description="RQ Dashboard FastAPI")
    subparsers = parser.add_subparsers(dest="command")

    # Default 'serve' behavior (also runs when no subcommand given)
    serve_parser = subparsers.add_parser("serve", help="Start the dashboard server")
    _add_serve_args(serve_parser)

    # generate-token subcommand
    subparsers.add_parser(
        "generate-token", help="Generate a token and its SHA-256 hash"
    )

    # Also add serve args to the main parser for backwards compatibility
    _add_serve_args(parser)

    args = parser.parse_args()

    if args.command == "generate-token":
        _generate_token()
    else:
        _serve(args)


def _add_serve_args(parser):
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
    parser.add_argument(
        "--auth-config",
        default=os.getenv("RQ_DASH_AUTH_CONFIG"),
        help="Path to auth YAML config file (default: $RQ_DASH_AUTH_CONFIG)",
    )


def _serve(args):
    app = FastAPI()
    dashboard = RedisQueueDashboard(
        redis_url=args.redis_url,
        prefix=args.prefix,
        auth_config=args.auth_config,
    )
    app.mount(args.prefix, dashboard)

    uvicorn.run(app, host=args.host, port=args.port)


def _generate_token():
    from rq_dashboard_fast.utils.auth import generate_token_pair

    token, token_hash = generate_token_pair()
    print(f"Token (give to the user):  {token}")
    print(f"Hash  (put in config):     {token_hash}")
