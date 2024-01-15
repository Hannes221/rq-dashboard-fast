from fastapi import APIRouter
from utils.redis_conn import queue, redis

router = APIRouter()


@router.get("/queues", response_model=list)
def get_queues():
    queues = queue.all(connection=redis)
    
    return queues