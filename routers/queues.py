from utils.redis_conn import queue, redis

def get_queues():
    queues = queue.all(connection=redis)
    
    return queues