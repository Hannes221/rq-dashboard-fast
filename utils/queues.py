from redis import Redis
from utils.redis_conn import redis
from rq import Queue
from utils.job_registries import get_job_registry_stats_for_queue

def get_queues():
    queues = Queue.all(connection=Redis())
    
    return queues
    

def get_jobs_for_queue(queue_name):
    queue = Queue(queue_name, connection=redis)
    return get_job_registry_stats_for_queue(queue)

def delete_jobs_for_queue(queue_name):
    queue = Queue(queue_name, connection=redis)
    
    jobs = queue.get_job_ids()
    
    for job in jobs:
        queue.pop_job_id(job)
        
    return jobs