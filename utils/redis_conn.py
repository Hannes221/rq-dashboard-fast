from rq import Connection, Queue
from redis import Redis

redis = Redis()
queue = Queue(connection=redis)
