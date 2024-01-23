from utils.redis_conn import redis
from rq import Queue

def get_queues():
    queue = Queue(connection=redis)
    queues = queue.all(connection=redis)
    
    return queues