from fastapi import APIRouter
from rq import Worker, Connection
from utils.redis_conn import redis

router = APIRouter()


@router.get("/workers", response_model=list)
async def get_workers():
    workers = Worker.all(connection=redis)
    
    return workers