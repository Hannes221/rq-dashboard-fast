# RQ Dashboard FastAPI <span>&#x1F6E0;</span>

![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white) 
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)


`RQ Dashboard FastAPI` is a general purpose, lightweight FastAPI-based web frontend to monitor your RQ queues, jobs, and workers in real-time. 

## Example Usage
```python
from fastapi import FastAPI
from dashboard import RedisQueueDashboard

dashboard = RedisQueueDashboard("redis://redis:6379/", "/rq")

app = FastAPI()

app.mount("/rq", dashboard)
```

## Installing from PyPi
```
$ pip install rq-dashboard-fast
```

## Running the dashboard
Run the dashboard like this:
```
$ rq-dashboard-fast
* Running on http://127.0.0.1:8000
...
```

## Contributing
If you want to contribute, reach out or create a PR directly. 
