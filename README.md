# RQ Dashboard FastAPI <span>&#x1F6E0;</span>

![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
<br />
<br />
`RQ Dashboard FastAPI` is a general purpose, lightweight FastAPI-based web frontend to monitor your RQ queues, jobs, and workers in real-time.
Goal of this package is to ease integration into FastAPI-Applications and provide a Docker Image for convenience.

<img width="1069" alt="Screenshot 2024-02-09 at 18 14 13" src="https://github.com/Hannes221/rq-dashboard-fast/assets/115920878/81946105-5b02-4413-bdf1-7016c85ad14d">

<br />

Featured in Related Projects [Redis Queue Docs](https://github.com/rq/rq)

## Example Usage

```python
from fastapi import FastAPI
from rq_dashboard_fast import RedisQueueDashboard
import uvicorn

app = FastAPI()
dashboard = RedisQueueDashboard("redis://redis:6379/", "/rq")

app.mount("/rq", dashboard)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Access the Dashboard at

```
http://127.0.0.1:8000/rq
```

## Installing from PyPi

PyPi: [rq-dashboard-fast](https://pypi.org/project/rq-dashboard-fast/)

```
$ pip install rq-dashboard-fast
```

## Running Standalone

After installing, you can run the dashboard directly from the terminal:

```
$ rq-dashboard-fast
```

This starts the dashboard at `http://localhost:8000/rq` using Redis at `redis://localhost:6379`.

Available options:

```
$ rq-dashboard-fast --help
$ rq-dashboard-fast --redis-url redis://my-redis:6379 --port 9000
$ rq-dashboard-fast --host 127.0.0.1 --prefix /dashboard
```

| Flag | Default | Environment Variable |
|------|---------|---------------------|
| `--redis-url` | `redis://localhost:6379` | `REDIS_URL` |
| `--host` | `0.0.0.0` | `FASTAPI_HOST` |
| `--port` | `8000` | `FASTAPI_PORT` |
| `--prefix` | `/rq` | — |

## Running in Docker

1. You can run the RQ Dashboard FastAPI as a Docker container with custom Redis URL:

```
docker run -e REDIS_URL=<your_redis_url> hannes221/rq-dashboard-fast

```

Access the Dashboard at

```
http://127.0.0.1:8000/rq
```

To change change the port, you can specify the following flag:

```
docker run -e REDIS_URL=<your_redis_url>  -e FASTAPI_PORT=<your_fastapi_port> hannes221/rq-dashboard-fast
```

Replace <your_fastapi_port> with your desired FastAPI and host port.

2. You can use Docker Compose by creating a docker-compose.yml file:

```yml
services:
  dashboard:
    image: hannes221/rq-dashboard-fast
    ports:
      - '8000:8000'
    environment:
      - REDIS_URL=<your_redis_url>
```

Then run:

```
docker compose up
```

Access the Dashboard at

```
http://127.0.0.1:8000/rq
```

To change the part update the compose file:

```yml
services:
  dashboard:
    image: hannes221/rq-dashboard-fast
    ports:
      - '<your_fastapi_port>:<your_fastapi_port>'
    environment:
      - REDIS_URL=<your_redis_url>
      - FASTAPI_PORT=<your_fastapi_port>
```

Replace <your_fastapi_port> with your desired FastAPI and host port.

Docker Hub: [hannes221/rq-dashboard-fast](https://hub.docker.com/r/hannes221/rq-dashboard-fast)

## Github Repository

Github: [rq-dashboard-fast](https://github.com/Hannes221/rq-dashboard-fast)

```
$ pip install rq-dashboard-fast
```

## Planned Features

- [x] Data from rq-scheduler
- [x] More data about workers
- [x] Docker Image
- [x] Add pagination to jobs page
- [x] Data Export
- [ ] Statistics Tab
- [x] Run Standalone (Terminal)

## Contributing

If you want to contribute, reach out or create a PR directly.
