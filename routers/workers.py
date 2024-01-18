from rq import Worker
from utils.redis_conn import redis

def get_workers():
    workers = Worker.all(connection=redis)
    
    return workers